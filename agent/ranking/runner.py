import json
import logging
from typing import Optional

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
from agent.ranking.api_client import call_deepseek

logger = logging.getLogger(__name__)

BRAND_RANK_SYSTEM_PROMPT = """你是一个品牌排名查询助手。我会给你一段排名 JSON 数据和一个品牌名称，你需要找出该品牌在排名中的位置。

JSON 结构: {"rankings": [{"rank": 数字, "brand": "品牌名", ...}]}

逐个检查 rankings 数组中的每一项，将 "brand" 字段与目标品牌进行语义匹配（不区分大小写、中英文别名、简称全称）。

严格按以下格式输出（只输出一行，不要有任何额外文字）：
找到时: {brand}排名: 第{rank}名
找不到时: 未找到"{target_brand}"的排名信息

示例1:
输入: JSON 有 "brand": "华为", "rank": 2, 目标品牌: 华为
输出: 华为排名: 第2名

示例2:
输入: JSON 有 "brand": "Huawei", "rank": 1, 目标品牌: 华为
输出: Huawei排名: 第1名

示例3:
输入: JSON 没有华为, 目标品牌: 华为
输出: 未找到"华为"的排名信息"""

BRAND_RANK_MAX_RETRIES = 3


def _validate_brand_rank_output(output: str, brand_keyword: str) -> str | None:
    """Validate brand rank output. Returns error string or None if valid."""
    if not output:
        return "Empty output"
    if "排名" in output and "第" in output:
        return None
    if "未找到" in output:
        return None
    return (
        "Output format invalid. Must be either "
        "'{brand}排名: 第{N}名' or '未找到\"{brand}\"的排名信息'. "
        "Got: " + output[:120]
    )


class RankingRunner:
    def __init__(self, answer_text: str, brand_keyword: Optional[str] = None):
        self.answer_text = answer_text
        self.brand_keyword = brand_keyword
        self._rankings_json: Optional[dict] = None

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
                    self._rankings_json = json_data
                    table = rankings_to_markdown(json_data)
                    return "## 综合排名\n\n" + table if table else ""
                self._last_error = err
            else:
                self._last_error = f"Unable to parse JSON, got: {raw[:200]}..."
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
                    self._rankings_json = json_data
                    table = rankings_to_markdown(json_data)
                    return "## 综合排名\n\n" + table if table else ""

        logger.error("Ranking analysis failed after all retries")
        return ""

    def run_mention_order(self) -> str:
        """Generate mention-order ranking from answer_text, sorted by first appearance."""
        if not self._rankings_json or not self.answer_text:
            return ""

        rankings = self._rankings_json.get("rankings", [])
        if not rankings:
            return ""

        text_lower = self.answer_text.lower()
        brand_positions: list[tuple[str, int, str]] = []
        self._mention_order: dict[str, tuple[int, str]] = {}

        for item in rankings:
            brand = item.get("brand", "")
            if not brand:
                continue
            pos = text_lower.find(brand.lower())
            if pos >= 0:
                start = max(0, pos - 20)
                end = min(len(self.answer_text), pos + len(brand) + 20)
                snippet = self.answer_text[start:end].replace("\n", " ").strip()
                if start > 0:
                    snippet = "..." + snippet
                if end < len(self.answer_text):
                    snippet = snippet + "..."
            else:
                snippet = "（未在正文中找到）"
                pos = 999999

            brand_positions.append((brand, pos, snippet))

        brand_positions.sort(key=lambda x: x[1])

        for i, (brand, _pos, snippet) in enumerate(brand_positions, 1):
            self._mention_order[brand.lower()] = (i, snippet)

        lines = [
            "## 提及顺序排名",
            "",
            "按品牌在 AI 回答正文中首次出现的先后顺序排列：",
            "",
            "| 提及顺序 | 品牌 | 上下文 |",
            "|---------|------|--------|",
        ]
        for i, (brand, _pos, snippet) in enumerate(brand_positions, 1):
            snippet_escaped = snippet.replace("|", "\\|")
            lines.append(f"| {i} | {brand} | {snippet_escaped} |")

        return "\n".join(lines)

    def _find_mention_order_rank(self) -> str:
        """Look up brand's position in mention-order ranking (local, no AI).
        Uses fuzzy matching: exact → case-insensitive → substring."""
        if not self.brand_keyword:
            return ""
        mention = getattr(self, "_mention_order", {})
        if not mention:
            return ""

        kw = self.brand_keyword.strip().lower()

        # 1. Exact match
        found = mention.get(kw)
        if found:
            rank, _ = found
            return f"提及顺序第{rank}名"

        # 2. Case-insensitive key iteration
        for key, (rank, _) in mention.items():
            if key.strip().lower() == kw:
                return f"提及顺序第{rank}名"

        # 3. Substring match (brand_keyword in key, or key in brand_keyword)
        for key, (rank, _) in mention.items():
            kl = key.strip().lower()
            if kw in kl or kl in kw:
                return f"提及顺序第{rank}名"

        return "提及顺序未找到"

    async def _find_comprehensive_rank(self) -> str:
        """Find the rank of the specified brand in comprehensive rankings via AI with harness retry."""
        if not self.brand_keyword:
            return ""

        rankings = self._rankings_json.get("rankings", [])
        if not rankings:
            return ""

        nl = chr(10)
        rankings_json_str = json.dumps(self._rankings_json, ensure_ascii=False, indent=2)
        last_error: str | None = None

        for attempt in range(BRAND_RANK_MAX_RETRIES):
            try:
                user_prompt = (
                    "Ranking data:" + nl
                    + rankings_json_str
                    + nl + nl + "Target brand: "
                    + self.brand_keyword
                )
                if last_error and attempt > 0:
                    user_prompt += (
                        nl + nl + "[Error Feedback] Previous attempt failed: "
                        + last_error
                        + nl + "Please correct and output EXACTLY in the required format."
                    )

                result = call_deepseek(BRAND_RANK_SYSTEM_PROMPT, user_prompt)
                output = result.strip()
                logger.info(
                    "Brand rank attempt %d/%d for '%s': %s",
                    attempt + 1, BRAND_RANK_MAX_RETRIES, self.brand_keyword, output,
                )

                err = _validate_brand_rank_output(output, self.brand_keyword)
                if not err:
                    return output

                last_error = err
                logger.warning(
                    "Brand rank retry %d/%d: %s",
                    attempt + 1, BRAND_RANK_MAX_RETRIES, last_error,
                )

            except Exception as e:
                last_error = "API call failed: " + str(e)
                logger.warning(
                    "Brand rank retry %d/%d: %s",
                    attempt + 1, BRAND_RANK_MAX_RETRIES, last_error,
                )

        logger.error(
            "Brand rank failed after %d retries for '%s'",
            BRAND_RANK_MAX_RETRIES, self.brand_keyword,
        )
        return "未找到\"" + self.brand_keyword + "\"的排名信息"

    async def find_brand_rank(self) -> str:
        """Return brand's position in both comprehensive and mention-order rankings."""
        comp = await self._find_comprehensive_rank()
        mention = self._find_mention_order_rank()
        parts = [p for p in [comp, mention] if p]
        return "，".join(parts)
