import asyncio
import json
from pathlib import Path

from agent.harness.tool_registry import ToolRegistry
from agent.harness.context import AgentContext
from agent.harness.timeout import TimeoutManager
from agent.harness.errors import TimeoutExceededError
from agent.harness.logger import get_logger, log_event
from agent.platforms import resolve_platforms, Platform
from agent.tools.browser import BrowserTool
from agent.tools.navigation import NavigationTool
from agent.tools.input import InputTool
from agent.tools.screenshot import ScreenshotTool
from agent.tools.sidebar import SidebarTool

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent.parent / "backend" / "data" / "screenshots"

logger = get_logger(__name__)


def emit(msg: dict):
    print(json.dumps(msg, ensure_ascii=False), flush=True)


class Runner:
    def __init__(self, task_id: str, query: str, headless: bool = False,
                 brand_keyword: str | None = None, platforms: list[str] | None = None):
        self.task_id = task_id
        self.query = query
        self.headless = headless
        self.brand_keyword = brand_keyword
        self.platforms = resolve_platforms(platforms)
        self.ctx = AgentContext(task_id=task_id, query=query)
        self.timeout_mgr = TimeoutManager(default_timeout=720.0)

        self.tool_registry = ToolRegistry()
        self._register_tools()

    def _register_tools(self):
        self.tool_registry.register(BrowserTool())
        self.tool_registry.register(NavigationTool())
        self.tool_registry.register(InputTool())
        self.tool_registry.register(ScreenshotTool(SCREENSHOTS_DIR))
        self.tool_registry.register(SidebarTool())

    async def run(self) -> dict:
        log_event(logger, "runner_start", task_id=self.task_id, query=self.query,
                  platforms=[p.key for p in self.platforms])

        # ── Input filter harness ──
        from agent.harness.input_filter import InputFilter

        f = InputFilter()
        filter_result = f.check(self.query)
        if not filter_result["valid"]:
            emit({
                "type": "error",
                "status": "failed",
                "error": filter_result["reason"],
            })
            return {"status": "failed", "error": filter_result["reason"]}
        query = filter_result["sanitized"]
        self.ctx.query = query

        try:
            async with self.timeout_mgr.with_timeout(720):
                # ── Step 1: Launch browser once ──
                emit({
                    "type": "progress", "step": "launch",
                    "message": "正在启动浏览器...", "progress": 0,
                })
                browser_tool = self.tool_registry.get_tool("browser")
                launch_result = await browser_tool.execute(
                    self.ctx, {"action": "launch", "headless": self.headless}
                )
                if not launch_result.get("success"):
                    return {"status": "failed", "error": launch_result.get("error", "Browser launch failed")}

                nav_tool = self.tool_registry.get_tool("navigate")
                input_tool = self.tool_registry.get_tool("input")
                sidebar_tool = self.tool_registry.get_tool("sidebar")
                screenshot_tool = self.tool_registry.get_tool("screenshot")

                # ── Step 2: Run each platform in its own browser tab ──
                all_results: list[dict] = []
                total_platforms = len(self.platforms)
                base_progress = 5  # after launch
                progress_per_platform = 90 / total_platforms  # 5..95 range

                for idx, platform in enumerate(self.platforms):
                    p_start = base_progress + idx * progress_per_platform
                    platform_key = platform.key

                    log_event(logger, "platform_start", task_id=self.task_id, platform=platform_key)

                    # Open new tab for platform (first platform reuses the initial page)
                    if idx == 0:
                        page = self.ctx.page
                    else:
                        page = await self.ctx.context.new_page()
                        self.ctx.page = page
                    logger.info(f"Platform '{platform_key}' using page: {page.url or 'about:blank'}")

                    # Navigate
                    emit({
                        "type": "progress", "step": f"navigate_{platform_key}",
                        "message": f"正在打开 {platform.name} 官网...",
                        "progress": int(p_start + progress_per_platform * 0.05),
                    })
                    await nav_tool.execute(self.ctx, {"url": platform.url})
                    await nav_tool.execute(self.ctx, {"action": "wait_loaded"})

                    # Login check
                    emit({
                        "type": "progress", "step": f"login_{platform_key}",
                        "message": f"检查 {platform.name} 登录状态...",
                        "progress": int(p_start + progress_per_platform * 0.1),
                    })
                    login_result = await input_tool.execute(
                        self.ctx, {"action": "wait_for_login", "platform": platform_key}
                    )
                    if not login_result.get("success"):
                        logger.warning(f"{platform.name} login check failed, continuing anyway")

                    # Type and submit query
                    emit({
                        "type": "progress", "step": f"input_{platform_key}",
                        "message": f"正在向 {platform.name} 提交问题...",
                        "progress": int(p_start + progress_per_platform * 0.3),
                    })
                    submit_result = await input_tool.execute(
                        self.ctx, {"action": "type_and_submit", "text": query, "platform": platform_key}
                    )
                    if not submit_result.get("success"):
                        logger.error(f"{platform.name} submit failed: {submit_result.get('error')}")
                        continue

                    # Wait for response
                    emit({
                        "type": "progress", "step": f"wait_{platform_key}",
                        "message": f"正在等待 {platform.name} 回答生成...",
                        "progress": int(p_start + progress_per_platform * 0.45),
                    })
                    await input_tool.execute(self.ctx, {"action": "wait_for_response"})

                    # Collapse sidebar (best-effort)
                    emit({
                        "type": "progress", "step": f"sidebar_{platform_key}",
                        "message": f"正在收起 {platform.name} 侧边栏...",
                        "progress": int(p_start + progress_per_platform * 0.7),
                    })
                    await sidebar_tool.execute(self.ctx, {"action": "collapse", "platform": platform_key})

                    # Screenshot (only for the first platform)
                    screenshot_path = ""
                    if idx == 0:
                        emit({
                            "type": "progress", "step": "screenshot",
                            "message": "正在进行长截图...",
                            "progress": int(p_start + progress_per_platform * 0.8),
                        })
                        ss_result = await screenshot_tool.execute(self.ctx, {"action": "fullpage"})
                        if ss_result.get("success"):
                            screenshot_path = ss_result.get("path", "")

                    # Extract response
                    emit({
                        "type": "progress", "step": f"extract_{platform_key}",
                        "message": f"正在提取 {platform.name} 回复内容...",
                        "progress": int(p_start + progress_per_platform * 0.9),
                    })
                    extract_result = await input_tool.execute(
                        self.ctx, {"action": "extract_response", "platform": platform_key}
                    )
                    if extract_result.get("success"):
                        all_results.append({
                            "platform": platform_key,
                            "platform_name": platform.name,
                            "screenshot_path": screenshot_path,
                            "response_text": extract_result.get("response_text", ""),
                            "thinking_text": extract_result.get("thinking_text", ""),
                            "answer_text": extract_result.get("answer_text", ""),
                            "answer_html": extract_result.get("answer_html", ""),
                            "sources_json": extract_result.get("sources_json", ""),
                        })

                    log_event(logger, "platform_done", task_id=self.task_id, platform=platform_key)

                # ── Step 3: Combine results ──
                if not all_results:
                    emit({
                        "type": "error", "status": "failed",
                        "error": "所有平台均未能获取结果",
                    })
                    return {"status": "failed", "error": "所有平台均未能获取结果"}

                combined = self._combine_results(all_results)

                # ── Step 4: Ranking analysis ──
                emit({
                    "type": "progress", "step": "ranking",
                    "message": "正在分析品牌排名...",
                    "progress": 97,
                })

                ranking_table = ""
                brand_rank = ""
                answer_text = combined.get("answer_text", "")
                if answer_text:
                    from agent.ranking.runner import RankingRunner
                    ranking_runner = RankingRunner(answer_text, brand_keyword=self.brand_keyword)
                    comprehensive_table = await ranking_runner.run()
                    mention_order_table = ranking_runner.run_mention_order()

                    ranking_table = comprehensive_table
                    if mention_order_table:
                        ranking_table = comprehensive_table + "\n\n" + mention_order_table

                    if self.brand_keyword:
                        brand_rank = await ranking_runner.find_brand_rank()

                # ── Step 5: Emit final result ──
                # Build platform_results for per-platform UI display
                platform_results = []
                for r in all_results:
                    platform_results.append({
                        "platform": r["platform"],
                        "platform_name": r["platform_name"],
                        "answer_text": r.get("answer_text", ""),
                        "answer_html": r.get("answer_html", ""),
                        "thinking_text": r.get("thinking_text", ""),
                        "sources_json": r.get("sources_json", ""),
                    })

                emit({
                    "type": "result",
                    "status": "completed",
                    "screenshot": combined.get("screenshot_path", ""),
                    "response_text": combined.get("response_text", ""),
                    "thinking_text": combined.get("thinking_text", ""),
                    "answer_text": combined.get("answer_text", ""),
                    "answer_html": combined.get("answer_html", ""),
                    "sources_json": combined.get("sources_json", ""),
                    "ranking_table": ranking_table,
                    "brand_rank": brand_rank,
                    "platform_results": json.dumps(platform_results, ensure_ascii=False),
                })

                log_event(logger, "runner_completed", task_id=self.task_id)
                return {"status": "completed", "screenshot": combined.get("screenshot_path", "")}

        except TimeoutExceededError:
            emit({
                "type": "error", "status": "failed",
                "error": "Task timed out after 720s",
            })
            return {"status": "failed", "error": "Task timed out"}
        except Exception as e:
            log_event(logger, "runner_error", task_id=self.task_id, error=str(e))
            emit({
                "type": "error", "status": "failed",
                "error": str(e),
            })
            return {"status": "failed", "error": str(e)}
        finally:
            await self._cleanup()

    def _combine_results(self, all_results: list[dict]) -> dict:
        """Combine results from multiple platforms into a single result dict.

        Concatenates content from all platforms with platform headers.
        The first platform's screenshot is used as the primary screenshot.
        """
        if len(all_results) == 1:
            return all_results[0]

        parts_response: list[str] = []
        parts_thinking: list[str] = []
        parts_answer: list[str] = []
        parts_html: list[str] = []
        all_sources: list[dict] = []

        for r in all_results:
            p_name = r["platform_name"]

            if r.get("thinking_text"):
                parts_thinking.append(f"【{p_name}】\n{r['thinking_text']}")
            if r.get("answer_text"):
                parts_answer.append(f"【{p_name}】\n{r['answer_text']}")
            if r.get("answer_html"):
                parts_html.append(f"<!-- {p_name} -->\n{r['answer_html']}")

            # Merge sources with platform tag
            sources_str = r.get("sources_json", "")
            if sources_str:
                try:
                    sources_list = json.loads(sources_str)
                    for s in sources_list:
                        s["platform"] = p_name
                    all_sources.extend(sources_list)
                except (json.JSONDecodeError, TypeError):
                    pass

        combined_response = "\n\n".join(parts_thinking + parts_answer)
        if not combined_response:
            combined_response = "\n\n".join(parts_answer)

        return {
            "screenshot_path": all_results[0].get("screenshot_path", ""),
            "response_text": combined_response,
            "thinking_text": "\n\n".join(parts_thinking),
            "answer_text": "\n\n".join(parts_answer),
            "answer_html": "\n\n".join(parts_html),
            "sources_json": json.dumps(all_sources, ensure_ascii=False) if all_sources else "",
        }

    async def _cleanup(self):
        try:
            if self.ctx.browser:
                await self.ctx.browser.close()
        except Exception:
            pass
        try:
            pw = self.ctx.extra.pop("playwright", None)
            if pw:
                await pw.stop()
        except Exception:
            pass
