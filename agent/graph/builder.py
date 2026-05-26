"""Build the LangGraph StateGraph for the DeepSeek search agent."""

from langgraph.graph import StateGraph, START, END

from agent.graph.state import AgentGraphState
from agent.graph.nodes import (
    make_launch_node,
    make_navigate_node,
    make_wait_loaded_node,
    make_login_node,
    make_input_node,
    make_wait_response_node,
    make_sidebar_node,
    make_screenshot_node,
    make_extract_node,
    make_handle_error_node,
)
from agent.harness.tool_registry import ToolRegistry
from agent.harness.context import AgentContext


def _make_router(next_node: str):
    """Return a routing function that checks for errors."""
    def router(state: AgentGraphState) -> str:
        if state.get("error"):
            return "handle_error"
        return next_node
    return router


def create_agent_graph(registry: ToolRegistry, ctx: AgentContext):
    """Build and compile the agent state graph."""
    graph = StateGraph(AgentGraphState)

    # Add nodes
    graph.add_node("launch", make_launch_node(registry, ctx))
    graph.add_node("navigate", make_navigate_node(registry, ctx))
    graph.add_node("wait_loaded", make_wait_loaded_node(registry, ctx))
    graph.add_node("login", make_login_node(registry, ctx))
    graph.add_node("input", make_input_node(registry, ctx))
    graph.add_node("wait_response", make_wait_response_node(registry, ctx))
    graph.add_node("sidebar", make_sidebar_node(registry, ctx))
    graph.add_node("screenshot", make_screenshot_node(registry, ctx))
    graph.add_node("extract", make_extract_node(registry, ctx))
    graph.add_node("handle_error", make_handle_error_node(registry, ctx))

    # Entry
    graph.add_edge(START, "launch")

    # Linear chain with error routing for non-skippable steps.
    # Sidebar is the only step that tolerates failure — it always proceeds.
    error_checked = [
        ("launch", "navigate"),
        ("navigate", "wait_loaded"),
        ("wait_loaded", "login"),
        ("login", "input"),
        ("input", "wait_response"),
        ("wait_response", "sidebar"),
        ("screenshot", "extract"),
        ("extract", END),
    ]

    for src, dst in error_checked:
        next_key = dst if isinstance(dst, str) else "__end__"
        mapping = {"handle_error": "handle_error", next_key: dst}
        graph.add_conditional_edges(src, _make_router(next_key), mapping)

    # Sidebar always proceeds to screenshot (allow_failure)
    graph.add_edge("sidebar", "screenshot")

    # handle_error terminates
    graph.add_edge("handle_error", END)

    return graph.compile()
