from dataclasses import dataclass


@dataclass
class PlanStep:
    id: str
    description: str
    goal: str
    timeout: float = 60.0
    allow_failure: bool = False


@dataclass
class Plan:
    name: str
    steps: list[PlanStep]


def create_ranking_plan() -> Plan:
    return Plan(
        name="brand_ranking",
        steps=[
            PlanStep(
                id="generate_ranking",
                description="分析文本并生成品牌排名 JSON...",
                goal="调用 DeepSeek API 提取品牌排名，输出 JSON 格式",
                allow_failure=False,
            ),
        ],
    )
