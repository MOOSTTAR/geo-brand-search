import logging
import asyncio

from agent.harness.tool_registry import ToolRegistry
from agent.harness.context import AgentContext
from agent.harness.state import StepResult
from agent.harness.errors import MaxIterationsExceeded
from agent.harness.logger import log_event
from agent.react.prompt import DEEPSEEK_STATE_MACHINE


class ReactLoop:
    """ReAct loop: Thought → Action → Observation, driven by a state machine.

    Each iteration:
      1. Thought: determine current state from page context
      2. Action: execute the tool mapped to that state
      3. Observation: check result, transition to next state
    """

    def __init__(self, tool_registry: ToolRegistry, context: AgentContext, logger: logging.Logger):
        self.tools = tool_registry
        self.ctx = context
        self.logger = logger
        self.max_iterations = 15

    async def run(self, goal: str, start_state: str = "navigate") -> StepResult:
        """Execute the state machine from start_state until 'done' or failure."""
        current_state = start_state
        state_machine = DEEPSEEK_STATE_MACHINE

        for iteration in range(self.max_iterations):
            if current_state not in state_machine:
                return StepResult(
                    step_id=current_state,
                    success=False,
                    error=f"Unknown state: {current_state}",
                )

            rule = state_machine[current_state]

            # 1. Thought — resolve parameters
            tool_name = rule["action"]
            params = dict(rule["params"])
            for k, v in params.items():
                if isinstance(v, str) and "{query}" in v:
                    params[k] = v.replace("{query}", self.ctx.query)

            log_event(self.logger, "react_iteration",
                      iteration=iteration,
                      state=current_state,
                      action=tool_name,
                      params=str(params))

            # 2. Action — execute the tool
            try:
                tool = self.tools.get_tool(tool_name)
                result = await tool.execute(self.ctx, params)
            except Exception as e:
                log_event(self.logger, "react_action_error",
                          state=current_state, action=tool_name, error=str(e))

                if "retry_on" in rule:
                    await asyncio.sleep(1)
                    continue
                return StepResult(
                    step_id=current_state,
                    success=False,
                    error=str(e),
                )

            # 3. Observation — check result
            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error")
                log_event(self.logger, "react_action_failed",
                          state=current_state, error=error_msg)

                if "retry_on" in rule:
                    await asyncio.sleep(1)
                    continue
                return StepResult(
                    step_id=current_state,
                    success=False,
                    error=error_msg,
                    details=result,
                )

            # Transition to next state
            next_state = rule.get("next", "done")
            if next_state == "done":
                return StepResult(
                    step_id=current_state,
                    success=True,
                    description=f"Completed: {current_state}",
                    details=result,
                )

            current_state = next_state

        raise MaxIterationsExceeded(f"ReAct loop exceeded {self.max_iterations} iterations at state '{current_state}'")
