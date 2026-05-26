import asyncio
from pathlib import Path

from agent.harness.tool_registry import ToolRegistry
from agent.harness.state import AgentStatus, AgentState, StepResult
from agent.harness.context import AgentContext
from agent.harness.timeout import TimeoutManager
from agent.harness.errors import TimeoutExceededError
from agent.harness.logger import get_logger, log_event
from agent.planner.templates import create_deepseek_plan
from agent.planner.executor import PlanExecutor
from agent.react.loop import ReactLoop
from agent.tools.browser import BrowserTool
from agent.tools.navigation import NavigationTool
from agent.tools.input import InputTool
from agent.tools.screenshot import ScreenshotTool
from agent.tools.sidebar import SidebarTool

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent.parent / "backend" / "data" / "screenshots"

logger = get_logger(__name__)


def emit(msg: dict):
    """Write a JSON message to stdout for the backend to consume."""
    import json
    print(json.dumps(msg, ensure_ascii=False), flush=True)


class Runner:
    def __init__(self, task_id: str, query: str, headless: bool = False):
        self.task_id = task_id
        self.query = query
        self.headless = headless
        self.ctx = AgentContext(task_id=task_id, query=query)
        self.status = AgentStatus()
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
        self.status.transition(AgentState.PLANNING)

        plan = create_deepseek_plan(self.query)
        self.status.total_steps = len(plan.steps)
        log_event(logger, "plan_created", steps=[s.id for s in plan.steps])

        try:
            async with self.timeout_mgr.with_timeout(720):
                self.status.transition(AgentState.EXECUTING)

                browser_tool = self.tool_registry.get_tool("browser")
                await browser_tool.execute(self.ctx, {"action": "launch", "headless": self.headless})

                react_loop = ReactLoop(self.tool_registry, self.ctx, logger)
                executor = PlanExecutor(emit)

                for i, step in enumerate(plan.steps):
                    self.status.current_step_index = i
                    self.status.progress = int((i / len(plan.steps)) * 100)

                    emit({
                        "type": "progress",
                        "step": step.id,
                        "message": step.description,
                        "progress": self.status.progress,
                    })

                    try:
                        result = await executor.execute_step(step, react_loop)
                    except TimeoutExceededError:
                        result = StepResult(
                            step_id=step.id,
                            success=False,
                            description=step.description,
                            error="Step timed out",
                        )

                    self.status.record_step(result)

                    if not result.success and not step.allow_failure:
                        emit({
                            "type": "error",
                            "status": "failed",
                            "error": result.error or "Step failed",
                            "step": step.id,
                        })
                        self.status.transition(AgentState.FAILED)
                        return {"status": "failed", "error": result.error}

                self.status.progress = 90
                screenshot_filename = f"{self.task_id}.png"

                # Screenshot already taken — now scroll + expand + extract full text
                emit({
                    "type": "progress",
                    "step": "extract",
                    "message": "正在提取回复内容...",
                    "progress": 93,
                })

                input_tool = self.tool_registry.get_tool("input")
                extract_result = await input_tool.execute(
                    self.ctx, {"action": "extract_response"}
                )
                response_text = extract_result.get("response_text", "") or ""
                thinking_text = extract_result.get("thinking_text", "") or ""
                answer_text = extract_result.get("answer_text", "") or ""
                answer_html = extract_result.get("answer_html", "") or ""

                self.status.transition(AgentState.COMPLETED)
                self.status.progress = 100

                emit({
                    "type": "result",
                    "status": "completed",
                    "screenshot": screenshot_filename,
                    "response_text": response_text,
                    "thinking_text": thinking_text,
                    "answer_text": answer_text,
                    "answer_html": answer_html,
                })
                log_event(logger, "runner_completed", task_id=self.task_id)
                return {"status": "completed", "screenshot": screenshot_filename}

        except TimeoutExceededError:
            self.status.transition(AgentState.TIMED_OUT)
            emit({
                "type": "error",
                "status": "failed",
                "error": "Task timed out after 720s",
            })
            return {"status": "failed", "error": "Task timed out"}
        except Exception as e:
            self.status.transition(AgentState.FAILED)
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
