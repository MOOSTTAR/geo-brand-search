import asyncio
import io
from typing import Any

from PIL import Image
import numpy as np

from agent.tools.base import BaseTool
from agent.harness.context import AgentContext
from agent.harness.logger import get_logger

logger = get_logger(__name__)

HIGH_VARIANCE_THRESHOLD = 35.0


def _check_sidebar_visible(image_bytes: bytes) -> tuple[bool, float]:
    """Check if sidebar is visible by max column-band variance."""
    img = Image.open(io.BytesIO(image_bytes)).convert("L")
    arr = np.array(img, dtype=np.float64)
    h = arr.shape[0]
    max_std = 0.0
    for x_start in range(0, min(260, arr.shape[1]), 20):
        band = arr[0:h, x_start:x_start + 20]
        band_std = float(band.std())
        if band_std > max_std:
            max_std = band_std
    return max_std > HIGH_VARIANCE_THRESHOLD, max_std


async def _capture_left_strip(page, width: int = 260, height: int = 600) -> bytes:
    viewport = page.viewport_size or {"width": 1920, "height": 1080}
    h = min(height, viewport["height"])
    return await page.screenshot(clip={"x": 0, "y": 0, "width": width, "height": h})


async def _get_sidebar_width(page) -> int:
    """Get the current width of the sidebar panel via DOM."""
    return await page.evaluate("""
        () => {
            const panel = document.querySelector('.dc04ec1d');
            if (!panel) return -1;
            return Math.round(panel.getBoundingClientRect().width);
        }
    """)


async def _get_top_icon_buttons(page) -> list[dict]:
    """Find small icon buttons at the top of the sidebar/left area.
    Only counts buttons in the left panel area (left < 300 to exclude
    far-right buttons like user menu, notifications etc).

    Returns list sorted left-to-right. When sidebar is expanded there are 2
    (search + collapse). When collapsed there are 3 (expand + search + ?).
    """
    return await page.evaluate("""
        () => {
            const results = [];
            const btns = document.querySelectorAll('[role="button"]');
            for (const btn of btns) {
                const r = btn.getBoundingClientRect();
                if (r.width === 0 || r.height === 0) continue;
                if (r.width > 50 || r.height > 50) continue;
                if (r.top > 80) continue;
                if (r.left > 300) continue;  // Only sidebar area
                const style = window.getComputedStyle(btn);
                if (style.display === 'none' || style.visibility === 'hidden') continue;
                if (parseFloat(style.opacity) < 0.5) continue;

                results.push({
                    x: Math.round(r.left + r.width / 2),
                    y: Math.round(r.top + r.height / 2),
                    left: Math.round(r.left),
                    top: Math.round(r.top),
                    w: Math.round(r.width),
                    h: Math.round(r.height),
                });
            }
            results.sort((a, b) => a.left - b.left);
            return results;
        }
    """)


class SidebarTool(BaseTool):
    name = "sidebar"
    description = "Find and collapse the page sidebar using ReAct-style icon button counting"

    async def execute(self, ctx: AgentContext, params: dict[str, Any]) -> dict[str, Any]:
        if not ctx.page:
            return {"success": False, "error": "No page available"}

        page = ctx.page
        await asyncio.sleep(0.5)

        # Step 1: Observe — check sidebar state via DOM
        sidebar_width = await _get_sidebar_width(page)
        logger.info(f"Sidebar panel width: {sidebar_width}px")
        if 0 <= sidebar_width < 50:
            logger.info("Sidebar already collapsed (DOM check)")
            return {"success": True, "message": "Sidebar already collapsed"}

        # Step 2: Observe — count top icon buttons
        # When expanded: 2 icon buttons (search=1st, collapse=2nd)
        # When collapsed: 3 icon buttons (expand=1st, search=2nd, ?=3rd)
        icon_buttons = await _get_top_icon_buttons(page)
        logger.info(f"Top icon buttons found: {len(icon_buttons)}")
        for i, b in enumerate(icon_buttons):
            logger.info(f"  [{i}] ({b['x']},{b['y']}) left={b['left']} top={b['top']} {b['w']}x{b['h']}")

        # Step 3: Reason — decide which button to click
        target_index = None
        if len(icon_buttons) == 2:
            # Sidebar expanded: 2nd button is collapse
            target_index = 1
            logger.info("Detected 2 icon buttons (sidebar expanded), will click 2nd one (collapse)")
        elif len(icon_buttons) == 3:
            # Sidebar collapsed but DOM check above should have caught this
            # If we got here, the DOM check didn't detect collapse — try 1st button anyway
            logger.info("Detected 3 icon buttons, sidebar may already be collapsed")
            return {"success": True, "message": "Sidebar appears already collapsed (3 icon buttons)"}
        else:
            logger.info(f"Unexpected number of icon buttons: {len(icon_buttons)}, trying rightmost")
            target_index = len(icon_buttons) - 1

        if target_index is None or target_index >= len(icon_buttons):
            return {"success": True, "message": "Could not determine which button to click"}

        # Step 4: Act — click the target button
        target = icon_buttons[target_index]
        logger.info(f"Clicking icon button [{target_index}] at ({target['x']},{target['y']})")

        try:
            await page.mouse.click(target["x"], target["y"])
        except Exception as e:
            logger.warning(f"Click failed: {e}")
            return {"success": True, "message": f"Click failed: {e}"}

        await asyncio.sleep(1.0)

        # Step 5: Observe — verify sidebar collapsed
        new_width = await _get_sidebar_width(page)
        logger.info(f"After click: sidebar width={new_width}px (was {sidebar_width}px)")

        if 0 <= new_width < 50:
            logger.info(f"Sidebar collapsed successfully! Width {sidebar_width}px -> {new_width}px")
            return {"success": True, "message": "Sidebar collapsed (DOM confirmed)"}

        # If DOM not available, fall back to pixel analysis
        try:
            strip = await _capture_left_strip(page)
            visible, max_std = _check_sidebar_visible(strip)
            logger.info(f"After click pixel check: visible={visible}, max_band_std={max_std:.1f}")
            if not visible:
                logger.info("Sidebar collapsed (pixel confirmed)")
                return {"success": True, "message": "Sidebar collapsed (pixel confirmed)"}
        except Exception as e:
            logger.warning(f"Pixel verification failed: {e}")

        # Step 6: If still not collapsed, try the other icon button (if we clicked wrong one)
        if len(icon_buttons) == 2:
            other_index = 0  # Try the 1st button (search) as last resort
            other = icon_buttons[other_index]
            logger.info(f"First attempt didn't work, trying other button [{other_index}] at ({other['x']},{other['y']})")
            try:
                await page.mouse.click(other["x"], other["y"])
                await asyncio.sleep(1.0)
                new_width2 = await _get_sidebar_width(page)
                if 0 <= new_width2 < 50:
                    logger.info(f"Sidebar collapsed on retry! Width {sidebar_width}px -> {new_width2}px")
                    return {"success": True, "message": "Sidebar collapsed (retry DOM confirmed)"}
            except Exception as e:
                logger.warning(f"Retry click failed: {e}")

        logger.info("Sidebar collapse not confirmed")
        return {"success": True, "message": "Sidebar collapse not confirmed"}
