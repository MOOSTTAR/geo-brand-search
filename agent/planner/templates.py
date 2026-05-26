from dataclasses import dataclass, field

from agent.harness.retry import RetryPolicy


@dataclass
class PlanStep:
    id: str
    description: str
    goal: str
    timeout: float = 30.0
    allow_failure: bool = False
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)


@dataclass
class Plan:
    name: str
    steps: list[PlanStep]


def create_deepseek_plan(query: str) -> Plan:
    return Plan(
        name="deepseek_search",
        steps=[
            PlanStep(
                id="navigate",
                description="正在打开 DeepSeek 官网...",
                goal="导航到 https://chat.deepseek.com",
                timeout=20,
                allow_failure=False,
            ),
            PlanStep(
                id="login",
                description="请在浏览器中登录 DeepSeek 账号，登录后自动继续...",
                goal="持续检测页面登录状态：登录页则等待，检测到聊天输入框则继续",
                timeout=600,
                allow_failure=False,
            ),
            PlanStep(
                id="input",
                description=f"正在输入问题: {query[:50]}{'...' if len(query) > 50 else ''}",
                goal="在输入框中输入用户问题并提交",
                timeout=30,
                allow_failure=False,
            ),
            PlanStep(
                id="wait",
                description="正在等待 DeepSeek 回答生成...",
                goal="检测回答是否生成完成",
                timeout=180,
                allow_failure=False,
            ),
            PlanStep(
                id="sidebar",
                description="正在收起侧边栏...",
                goal="点击侧边栏收起按钮以隐藏对话列表",
                timeout=20,
                allow_failure=True,
            ),
            PlanStep(
                id="screenshot",
                description="正在进行长截图...",
                goal="执行全页截图并保存到指定目录",
                timeout=15,
                allow_failure=False,
            ),
        ],
    )
