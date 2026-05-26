from typing import Any

from agent.tools.base import BaseTool


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not registered. Available: {list(self._tools.keys())}")
        return tool

    def list_tools(self) -> list[dict[str, Any]]:
        return [t.schema for t in self._tools.values()]
