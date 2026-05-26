import logging

from agent.ranking.tools.llm_api import LLMApiTool
from agent.ranking.react.loop import ReactLoop
from agent.ranking.planner.templates import create_ranking_plan
from agent.ranking.planner.executor import PlanExecutor
from agent.ranking.harness.cleaner import (
    extract_json,
    validate_ranking,
    rankings_to_markdown,
    MAX_RETRIES,
)

logger = logging.getLogger(__name__)


class RankingRunner:
    def __init__(self, answer_text: str):
        self.answer_text = answer_text

    async def run(self) -> str:
        if not self.answer_text.strip():
            return ""

        tool_registry = {"llm": LLMApiTool()}
        react_loop = ReactLoop(tool_registry, self.answer_text)
        executor = PlanExecutor()

        for attempt in range(MAX_RETRIES):
            error_feedback = None if attempt == 0 else self._last_error
            raw = await react_loop.run(error_feedback=error_feedback)

            json_data = extract_json(raw)
            if json_data:
                err = validate_ranking(json_data)
                if not err:
                    return rankings_to_markdown(json_data)
                self._last_error = err
            else:
                self._last_error = f"无法解析为 JSON，收到: {raw[:200]}..."
            logger.warning(f"Ranking retry {attempt + 1}/{MAX_RETRIES}: {self._last_error}")

        # Final fallback: one-shot with error feedback
        tool = LLMApiTool()
        r = await tool.execute({
            "text": self.answer_text,
            "error_feedback": self._last_error,
        })
        if r.get("success"):
            json_data = extract_json(r["result"])
            if json_data:
                err = validate_ranking(json_data)
                if not err:
                    return rankings_to_markdown(json_data)

        logger.error("Ranking analysis failed after all retries")
        return ""
