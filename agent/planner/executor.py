from typing import Callable

from agent.planner.templates import PlanStep
from agent.harness.state import StepResult
from agent.harness.timeout import TimeoutManager
from agent.harness.logger import get_logger

logger = get_logger(__name__)


class PlanExecutor:
    """Executes a plan step by step, reporting progress via a callback."""

    def __init__(self, on_progress: Callable[[dict], None]):
        self.on_progress = on_progress

    async def execute_step(self, step: PlanStep, react_loop) -> StepResult:
        timeout_mgr = TimeoutManager(default_timeout=step.timeout)

        try:
            async with timeout_mgr.with_timeout(step.timeout):
                result = await react_loop.run(step.goal, start_state=step.id)
        except Exception as e:
            result = StepResult(
                step_id=step.id,
                success=False,
                description=step.description,
                error=str(e),
            )

        from agent.harness.logger import log_event
        log_event(logger, "step_executed",
                  step_id=step.id,
                  success=result.success,
                  error=result.error)

        return result
