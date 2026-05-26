from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    name: str
    description: str

    @property
    def schema(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description}

    @abstractmethod
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        ...
