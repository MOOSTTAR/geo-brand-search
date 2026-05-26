from abc import ABC, abstractmethod
from typing import Any

from agent.harness.context import AgentContext


class BaseTool(ABC):
    name: str
    description: str

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
        }

    @abstractmethod
    async def execute(self, ctx: AgentContext, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the tool. Returns a dict with at least {'success': bool}."""
        ...
