import asyncio
import json
from pathlib import Path

from agent.graph.builder import create_agent_graph
from agent.graph.state import AgentGraphState
from agent.harness.tool_registry import ToolRegistry
from agent.harness.context import AgentContext
from agent.harness.timeout import TimeoutManager
from agent.harness.errors import TimeoutExceededError
from agent.harness.logger import get_logger, log_event
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
    def __init__(self, task_id: str, query: str, headless: bool = False):
        self.task_id = task_id
        self.query = query
        self.headless = headless
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
        log_event(logger, "runner_start", task_id=self.task_id, query=self.query)

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

        initial_state: AgentGraphState = {
            "task_id": self.task_id,
            "query": query,
            "headless": self.headless,
            "progress": 0,
            "current_step": "start",
            "screenshot_path": None,
            "response_text": None,
            "thinking_text": None,
            "answer_text": None,
            "answer_html": None,
            "error": None,
        }

        try:
            async with self.timeout_mgr.with_timeout(720):
                graph = create_agent_graph(self.tool_registry, self.ctx)
                result = await graph.ainvoke(initial_state)

                if result.get("error"):
                    return {"status": "failed", "error": result["error"]}

                # Run ranking analysis before emitting result
                ranking_table = ""
                answer_text = result.get("answer_text", "")
                if answer_text:
                    from agent.ranking.runner import RankingRunner
                    emit({
                        "type": "progress",
                        "step": "ranking",
                        "message": "正在分析品牌排名...",
                        "progress": 97,
                    })
                    ranking_runner = RankingRunner(answer_text)
                    ranking_table = await ranking_runner.run()

                # Emit result now that ranking is done
                emit({
                    "type": "result",
                    "status": "completed",
                    "screenshot": result.get("screenshot_path", ""),
                    "response_text": result.get("response_text", ""),
                    "thinking_text": result.get("thinking_text", ""),
                    "answer_text": result.get("answer_text", ""),
                    "answer_html": result.get("answer_html", ""),
                    "ranking_table": ranking_table,
                })

                log_event(logger, "runner_completed", task_id=self.task_id)
                return {"status": "completed", "screenshot": result.get("screenshot_path", "")}

        except TimeoutExceededError:
            emit({
                "type": "error",
                "status": "failed",
                "error": "Task timed out after 720s",
            })
            return {"status": "failed", "error": "Task timed out"}
        except Exception as e:
            log_event(logger, "runner_error", task_id=self.task_id, error=str(e))
            emit({
                "type": "error",
                "status": "failed",
                "error": str(e),
            })
            return {"status": "failed", "error": str(e)}
        finally:
            await self._cleanup()

    async def _cleanup(self):
        try:
            if self.ctx.browser:
                await self.ctx.browser.close()
        except Exception:
            pass
