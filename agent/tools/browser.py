from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

from agent.tools.base import BaseTool
from agent.harness.context import AgentContext
from agent.harness.errors import BrowserError
from agent.harness.logger import get_logger

logger = get_logger(__name__)

USER_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "browser_data"


class BrowserTool(BaseTool):
    name = "browser"
    description = "Manage the Playwright browser lifecycle: launch or close"

    async def execute(self, ctx: AgentContext, params: dict[str, Any]) -> dict[str, Any]:
        action = params.get("action", "launch")

        if action == "launch":
            return await self._launch(ctx, params)
        elif action == "close":
            return await self._close(ctx)
        else:
            return {"success": False, "error": f"Unknown browser action: {action}"}

    async def _launch(self, ctx: AgentContext, params: dict[str, Any]) -> dict[str, Any]:
        try:
            pw = await async_playwright().start()
            headless = params.get("headless", False)
            ctx.extra["playwright"] = pw

            USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

            ctx.context = await pw.chromium.launch_persistent_context(
                user_data_dir=str(USER_DATA_DIR),
                headless=headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
            )
            ctx.browser = ctx.context.browser

            if ctx.context.pages:
                ctx.page = ctx.context.pages[0]
            else:
                ctx.page = await ctx.context.new_page()

            logger.info(f"Browser launched (persistent context at {USER_DATA_DIR})")
            return {"success": True}
        except Exception as e:
            raise BrowserError(f"Failed to launch browser: {e}")

    async def _close(self, ctx: AgentContext) -> dict[str, Any]:
        try:
            if ctx.context:
                await ctx.context.close()
            pw = ctx.extra.pop("playwright", None)
            if pw:
                await pw.stop()
            ctx.browser = None
            ctx.context = None
            ctx.page = None
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
