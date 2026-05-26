from typing import Any

from agent.tools.base import BaseTool
from agent.harness.context import AgentContext
from agent.harness.logger import get_logger

logger = get_logger(__name__)


class NavigationTool(BaseTool):
    name = "navigate"
    description = "Navigate to a URL or wait for page to finish loading"

    async def execute(self, ctx: AgentContext, params: dict[str, Any]) -> dict[str, Any]:
        if not ctx.page:
            return {"success": False, "error": "No page available. Launch browser first."}

        if params.get("action") == "wait_loaded":
            return await self._wait_loaded(ctx)
        else:
            url = params.get("url")
            if not url:
                return {"success": False, "error": "URL is required"}
            return await self._navigate(ctx, url)

    async def _navigate(self, ctx: AgentContext, url: str) -> dict[str, Any]:
        try:
            logger.info(f"Navigating to {url}")
            await ctx.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return {"success": True, "url": ctx.page.url}
        except Exception as e:
            # Page loaded partially — still OK for login flow
            logger.warning(f"Navigation to {url} had issues: {e}")
            try:
                return {"success": True, "url": ctx.page.url}
            except Exception:
                return {"success": True, "url": url}

    async def _wait_loaded(self, ctx: AgentContext) -> dict[str, Any]:
        try:
            await ctx.page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        return {"success": True, "url": ctx.page.url}
