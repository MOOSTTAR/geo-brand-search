"""LangGraph node factories for the AI chat search agent.

Each factory returns an async function (state) -> partial state update.
Nodes communicate progress via stdout JSON Lines (the emit protocol).
"""

import json

from agent.graph.state import AgentGraphState
from agent.harness.tool_registry import ToolRegistry
from agent.harness.context import AgentContext
from agent.platforms import get_platform


def emit(msg: dict) -> None:
    print(json.dumps(msg, ensure_ascii=False), flush=True)


async def _run_tool(
    tool: object,
    ctx: AgentContext,
    params: dict,
    step_name: str,
    message: str,
    progress: int,
    *,
    allow_failure: bool = False,
) -> dict:
    """Execute a tool, emit progress, return state update.

    On failure: sets ``error`` in the return dict unless *allow_failure* is True.
    """
    emit({
        "type": "progress",
        "step": step_name,
        "message": message,
        "progress": progress,
    })
    try:
        result = await tool.execute(ctx, params)
        if not result.get("success"):
            if allow_failure:
                return {"progress": progress, "current_step": step_name}
            error_msg = result.get("error", f"{step_name} failed")
            return {"error": error_msg, "current_step": step_name, "progress": progress}
        return {"progress": progress, "current_step": step_name}
    except Exception as exc:
        if allow_failure:
            return {"progress": progress, "current_step": step_name}
        return {"error": str(exc), "current_step": step_name, "progress": progress}


# ---------------------------------------------------------------------------
# Node factories
# ---------------------------------------------------------------------------


def make_launch_node(registry: ToolRegistry, ctx: AgentContext):
    async def launch_node(state: AgentGraphState) -> dict:
        tool = registry.get_tool("browser")
        return await _run_tool(
            tool, ctx,
            {"action": "launch", "headless": state.get("headless", False)},
            "launch", "正在启动浏览器...", 0,
        )
    return launch_node


def make_navigate_node(registry: ToolRegistry, ctx: AgentContext):
    async def navigate_node(state: AgentGraphState) -> dict:
        platform_key = state.get("platform", "deepseek")
        platform = get_platform(platform_key)
        tool = registry.get_tool("navigate")
        return await _run_tool(
            tool, ctx,
            {"url": platform.url},
            "navigate", f"正在打开 {platform.name} 官网...", 5,
        )
    return navigate_node


def make_wait_loaded_node(registry: ToolRegistry, ctx: AgentContext):
    async def wait_loaded_node(state: AgentGraphState) -> dict:
        tool = registry.get_tool("navigate")
        return await _run_tool(
            tool, ctx,
            {"action": "wait_loaded"},
            "page_loading", "正在等待页面加载...", 10,
        )
    return wait_loaded_node


def make_login_node(registry: ToolRegistry, ctx: AgentContext):
    async def login_node(state: AgentGraphState) -> dict:
        platform_key = state.get("platform", "deepseek")
        platform = get_platform(platform_key)
        tool = registry.get_tool("input")
        return await _run_tool(
            tool, ctx,
            {"action": "wait_for_login", "platform": platform_key},
            "login", f"请在浏览器中登录 {platform.name} 账号，登录后自动继续...", 15,
        )
    return login_node


def make_input_node(registry: ToolRegistry, ctx: AgentContext):
    async def input_node(state: AgentGraphState) -> dict:
        query = state["query"]
        platform_key = state.get("platform", "deepseek")
        short = f"{query[:50]}{'...' if len(query) > 50 else ''}"
        tool = registry.get_tool("input")
        return await _run_tool(
            tool, ctx,
            {"action": "type_and_submit", "text": query, "platform": platform_key},
            "input", f"正在输入问题: {short}", 35,
        )
    return input_node


def make_wait_response_node(registry: ToolRegistry, ctx: AgentContext):
    async def wait_response_node(state: AgentGraphState) -> dict:
        tool = registry.get_tool("input")
        return await _run_tool(
            tool, ctx,
            {"action": "wait_for_response"},
            "wait", "正在等待 AI 回答生成...", 45,
        )
    return wait_response_node


def make_sidebar_node(registry: ToolRegistry, ctx: AgentContext):
    async def sidebar_node(state: AgentGraphState) -> dict:
        platform_key = state.get("platform", "deepseek")
        tool = registry.get_tool("sidebar")
        return await _run_tool(
            tool, ctx,
            {"action": "collapse", "platform": platform_key},
            "sidebar", "正在收起侧边栏...", 75,
            allow_failure=True,
        )
    return sidebar_node


def make_screenshot_node(registry: ToolRegistry, ctx: AgentContext):
    async def screenshot_node(state: AgentGraphState) -> dict:
        tool = registry.get_tool("screenshot")
        result = await _run_tool(
            tool, ctx,
            {"action": "fullpage"},
            "screenshot", "正在进行长截图...", 85,
        )
        screenshot_name = getattr(ctx, "screenshot_path", None)
        if screenshot_name:
            result["screenshot_path"] = screenshot_name
        return result
    return screenshot_node


def make_extract_node(registry: ToolRegistry, ctx: AgentContext):
    async def extract_node(state: AgentGraphState) -> dict:
        platform_key = state.get("platform", "deepseek")
        platform = get_platform(platform_key)
        emit({
            "type": "progress",
            "step": "extract",
            "message": f"正在提取{platform.name}回复内容...",
            "progress": 93,
        })
        tool = registry.get_tool("input")
        try:
            result = await tool.execute(ctx, {"action": "extract_response", "platform": platform_key})
        except Exception as exc:
            return {"error": str(exc), "current_step": "extract", "progress": 93}

        if not result.get("success"):
            return {"error": result.get("error", "extract failed"), "current_step": "extract", "progress": 93}

        screenshot_name = getattr(ctx, "screenshot_path", "") or ""

        return {
            "progress": 100,
            "current_step": "done",
            "screenshot_path": screenshot_name,
            "response_text": result.get("response_text", ""),
            "thinking_text": result.get("thinking_text", ""),
            "answer_text": result.get("answer_text", ""),
            "answer_html": result.get("answer_html", ""),
            "sources_json": result.get("sources_json", ""),
        }
    return extract_node


def make_handle_error_node(registry: ToolRegistry, ctx: AgentContext):
    async def handle_error_node(state: AgentGraphState) -> dict:
        error = state.get("error", "Unknown error")
        emit({
            "type": "error",
            "status": "failed",
            "error": error,
            "step": state.get("current_step", ""),
        })
        return {}
    return handle_error_node
