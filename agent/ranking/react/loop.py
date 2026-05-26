import logging

from agent.ranking.react.prompt import RANKING_STATE_MACHINE

logger = logging.getLogger(__name__)


class ReactLoop:
    def __init__(self, tool_registry: dict, answer_text: str):
        self.tools = tool_registry
        self.answer_text = answer_text
        self.max_iterations = 10

    async def run(self, start_state: str = "generate_ranking",
                  error_feedback: str | None = None) -> str:
        current_state = start_state
        context: dict = {}

        for iteration in range(self.max_iterations):
            if current_state == "done":
                return context.get("result", "")

            if current_state not in RANKING_STATE_MACHINE:
                return context.get("error", "Unknown state")

            rule = RANKING_STATE_MACHINE[current_state]
            tool = self.tools.get(rule["action"])
            if not tool:
                return f"Tool '{rule['action']}' not registered"

            params = dict(rule["params"])
            params["text"] = self.answer_text
            if error_feedback:
                params["error_feedback"] = error_feedback

            try:
                result = await tool.execute(params)
            except Exception as e:
                return f"ReAct step '{current_state}' error: {e}"

            if not result.get("success"):
                return result.get("error", f"Step '{current_state}' failed")

            context["result"] = result.get("result", "")
            current_state = rule.get("next", "done")

        return "ReAct loop exceeded max iterations"
