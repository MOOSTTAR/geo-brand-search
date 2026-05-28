import asyncio
from typing import Any

from agent.tools.base import BaseTool
from agent.harness.context import AgentContext
from agent.platforms import get_platform
from agent.harness.logger import get_logger

logger = get_logger(__name__)


class SidebarTool(BaseTool):
    name = "sidebar"
    description = "Find and collapse the page sidebar"

    async def execute(self, ctx: AgentContext, params: dict[str, Any]) -> dict[str, Any]:
        if not ctx.page:
            return {"success": False, "error": "No page available"}

        platform_key = params.get("platform", "deepseek")
        platform = get_platform(platform_key)

        await asyncio.sleep(0.5)

        success = await platform.collapse_sidebar(ctx.page)
        if success:
            return {"success": True, "message": "Sidebar collapsed"}
        else:
            return {"success": True, "message": "Sidebar collapse not confirmed or not applicable"}
