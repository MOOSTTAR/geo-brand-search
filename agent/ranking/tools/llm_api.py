import logging
from typing import Any

from agent.ranking.tools.base import BaseTool
from agent.ranking.api_client import call_deepseek

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业的品牌排名分析助手。根据用户提供的文本内容，提取所有品牌/产品，根据文本中的评价质量排名。

严格按以下 JSON 格式输出，不要包含任何其他文字：
```json
{
  "rankings": [
    {
      "rank": 1,
      "brand": "品牌/产品名称",
      "strengths": "核心优势（简洁）",
      "weaknesses": "主要不足（简洁）",
      "score": 9.5
    }
  ]
}
```

规则：
- rank 从 1 开始递增
- score 为 1-10 的数值，基于文本中的正面/负面描述打分
- strengths 和 weaknesses 从原文中总结，每个不超过 30 字
- 只输出 JSON，不要任何解释或附加文字"""


def _build_user_prompt(text: str, error_feedback: str | None = None) -> str:
    prompt = f"请分析以下文本，提取品牌排名并以 JSON 格式输出：\n\n{text}"
    if error_feedback:
        prompt += f"\n\n⚠️ 上一次输出的 JSON 有误：{error_feedback}\n请修正并重新输出正确的 JSON。"
    return prompt


class LLMApiTool(BaseTool):
    name = "llm"
    description = "调用 DeepSeek API 进行品牌排名分析，输出 JSON 格式"

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        text = params.get("text", "")
        error_feedback = params.get("error_feedback")

        if not text:
            return {"success": False, "error": "No text provided"}

        user_prompt = _build_user_prompt(text, error_feedback)

        try:
            result = call_deepseek(SYSTEM_PROMPT, user_prompt)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
