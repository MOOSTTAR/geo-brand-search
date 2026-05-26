"""JSON extraction, validation, and retry harness for ranking agent output."""

import json
import re
import logging

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ["rank", "brand", "strengths", "weaknesses", "score"]
MAX_RETRIES = 3


def extract_json(text: str) -> dict | None:
    """Extract a valid JSON object from AI response text."""
    # Direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # JSON code block
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Curly-brace block (greedy)
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    return None


def validate_ranking(data: dict) -> str | None:
    """Validate ranking JSON structure. Returns error string or None."""
    if not isinstance(data, dict):
        return "Response is not a JSON object"

    rankings = data.get("rankings")
    if not isinstance(rankings, list):
        return "Missing or invalid 'rankings' array"

    if len(rankings) == 0:
        return "'rankings' array is empty"

    for i, item in enumerate(rankings):
        if not isinstance(item, dict):
            return f"Item {i} is not an object"
        for field in REQUIRED_FIELDS:
            if field not in item:
                return f"Item {i} missing required field: '{field}'"

    return None


def rankings_to_markdown(data: dict) -> str:
    """Convert validated ranking JSON to a Markdown table."""
    rankings = data.get("rankings", [])
    if not rankings:
        return ""

    rows = ["| 排名 | 品牌 | 核心优势 | 主要不足 | 综合评分 |",
            "|------|------|----------|----------|----------|"]

    for r in rankings:
        rows.append(
            f"| {r['rank']} | {r['brand']} | {r['strengths']} | {r['weaknesses']} | {r['score']} |"
        )

    return "\n".join(rows)
