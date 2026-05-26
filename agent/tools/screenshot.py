import asyncio
import io
from pathlib import Path
from typing import Any

from PIL import Image

from agent.tools.base import BaseTool
from agent.harness.context import AgentContext
from agent.harness.logger import get_logger

logger = get_logger(__name__)

OVERLAP = 60


def _stitch(images: list[bytes]) -> bytes:
    if len(images) == 1:
        return images[0]
    imgs = [Image.open(io.BytesIO(b)) for b in images]
    w = max(img.width for img in imgs)
    total_h = sum(img.height for img in imgs) - OVERLAP * (len(imgs) - 1)
    canvas = Image.new("RGB", (w, total_h))
    y = 0
    for i, img in enumerate(imgs):
        canvas.paste(img, (0, y))
        y += img.height - (OVERLAP if i < len(imgs) - 1 else 0)
    out = io.BytesIO()
    canvas.save(out, format="PNG", optimize=True)
    return out.getvalue()


class ScreenshotTool(BaseTool):
    name = "screenshot"
    description = "Take a full-content long screenshot of SPA pages and save to disk"

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self, ctx: AgentContext, params: dict[str, Any]) -> dict[str, Any]:
        if not ctx.page:
            return {"success": False, "error": "No page available"}

        action = params.get("action", "fullpage")
        if action != "fullpage":
            return {"success": False, "error": f"Unknown screenshot action: {action}"}

        filename = f"{ctx.task_id}.png"
        filepath = self.output_dir / filename

        try:
            image_bytes = await self._capture_long(ctx)
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            logger.info(f"Screenshot saved: {filepath}")
            ctx.screenshot_path = filename
            return {"success": True, "path": filename}
        except Exception as e:
            logger.warning(f"Long screenshot failed, fallback full_page: {e}")
            try:
                await ctx.page.screenshot(path=str(filepath), full_page=True)
                ctx.screenshot_path = filename
                logger.info(f"Fallback screenshot saved: {filepath}")
                return {"success": True, "path": filename}
            except Exception as e2:
                return {"success": False, "error": f"Screenshot failed: {e2}"}

    async def _capture_long(self, ctx: AgentContext) -> bytes:
        page = ctx.page
        vp = page.viewport_size or {"width": 1920, "height": 1080}
        vp_h = vp["height"]

        # Hide fixed bottom elements (input box, toolbar) so they don't
        # appear duplicated in every strip. Tag them to restore later.
        await page.evaluate("""
            () => {
                // Find elements anchored to the bottom of the viewport
                const bottom = window.innerHeight;
                const all = document.querySelectorAll('*');
                const toHide = [];
                for (const el of all) {
                    const r = el.getBoundingClientRect();
                    const s = window.getComputedStyle(el);
                    // Fixed or sticky at the bottom, spanning most of the width
                    if (r.bottom >= bottom - 5 && r.top > bottom * 0.5 &&
                        r.width > 300 && r.height > 30 && r.height < 300) {
                        toHide.push(el);
                    }
                }
                // Also hide elements positioned fixed at page bottom
                for (const el of all) {
                    const s = window.getComputedStyle(el);
                    if (s.position === 'fixed' || s.position === 'sticky') {
                        const r = el.getBoundingClientRect();
                        if (r.bottom >= bottom - 10 && r.width > 200) {
                            if (!toHide.includes(el)) toHide.push(el);
                        }
                    }
                }
                for (const el of toHide) {
                    el.setAttribute('data-screenshot-hidden', el.style.display || '');
                    el.style.display = 'none';
                }
                return toHide.length;
            }
        """)
        await asyncio.sleep(0.3)

        try:
            # Re-measure after hiding bottom elements (content area may be taller)
            metrics = await page.evaluate("""
                () => {
                    let best = null;
                    let bestScore = 0;
                    const all = document.querySelectorAll('*');
                    for (const el of all) {
                        if (el.scrollHeight <= el.clientHeight + 5) continue;
                        const s = window.getComputedStyle(el);
                        if (s.overflowY === 'hidden' || s.overflowY === 'visible') continue;
                        const r = el.getBoundingClientRect();
                        if (r.width < 300 || r.height < 150) continue;
                        const score = el.scrollHeight * (r.left > 200 ? 2 : 1);
                        if (score > bestScore) {
                            bestScore = score;
                            best = el;
                        }
                    }

                    if (best) {
                        best.setAttribute('data-scroller', '1');
                        const r = best.getBoundingClientRect();
                        return {
                            mode: 'container',
                            scrollHeight: best.scrollHeight,
                            viewH: best.clientHeight,
                            clipX: Math.round(r.left),
                            clipY: Math.round(r.top),
                            clipW: Math.round(r.width),
                            clipH: Math.round(r.height),
                        };
                    }

                    const sh = Math.max(
                        document.documentElement.scrollHeight,
                        document.body.scrollHeight || 0
                    );
                    return {
                        mode: 'body',
                        scrollHeight: sh,
                        viewH: window.innerHeight,
                    };
                }
            """)

            mode = metrics["mode"]
            scroll_height = metrics["scrollHeight"]
            logger.info(
                f"Screenshot mode={mode}, scrollHeight={scroll_height}, "
                f"viewportHeight={vp_h}"
            )

            if mode == "container":
                clip_x = metrics["clipX"]
                clip_y = metrics["clipY"]
                clip_w = metrics["clipW"]
                clip_h = metrics["clipH"]

                strips = []
                captured_bottom = 0  # bottom edge of content already captured
                scroll_top = 0
                iteration = 0

                logger.info(f"Capturing long screenshot (bottom bar hidden), scrollHeight={scroll_height}")

                while captured_bottom < scroll_height:
                    # Scroll container to current position
                    await page.evaluate(f"""
                        () => {{
                            const el = document.querySelector('[data-scroller]');
                            if (el) el.scrollTop = {scroll_top};
                        }}
                    """)
                    await asyncio.sleep(0.35)

                    # Read back actual scrollTop (may differ at end of content)
                    actual_st = await page.evaluate(
                        "() => { const el = document.querySelector('[data-scroller]'); return el ? el.scrollTop : 0; }"
                    )

                    # Take viewport screenshot, clip to content area
                    full = await page.screenshot(type="png")
                    img = Image.open(io.BytesIO(full))
                    crop_x = max(0, clip_x)
                    crop_y = max(0, clip_y)
                    crop_w = min(clip_w, img.width - crop_x)
                    crop_h_val = min(clip_h, img.height - crop_y)
                    cropped = img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h_val))

                    # Visible range in content coordinates
                    visible_top = actual_st
                    visible_bottom = min(actual_st + clip_h, scroll_height)

                    if captured_bottom == 0:
                        # First strip — keep from top
                        crop_top = 0
                    else:
                        # Overlap with previously captured content
                        overlap = captured_bottom - visible_top
                        keep_overlap = min(OVERLAP, overlap) if overlap > 0 else 0
                        crop_top = max(0, overlap - keep_overlap)

                    # Bottom of this strip in image pixels
                    crop_bottom = visible_bottom - visible_top

                    # Crop to only the new portion
                    if crop_top > 0 or crop_bottom < clip_h:
                        cropped = cropped.crop((0, crop_top, clip_w, crop_bottom))

                    buf = io.BytesIO()
                    cropped.save(buf, format="PNG")
                    strips.append(buf.getvalue())

                    iteration += 1
                    logger.info(
                        f"  Strip {iteration}: scrollTop={actual_st}, "
                        f"visible=[{visible_top},{visible_bottom}], "
                        f"crop=[{crop_top},{crop_bottom}], "
                        f"height={crop_bottom - crop_top}px"
                    )

                    # Advance to next scroll position
                    captured_bottom = visible_bottom
                    if captured_bottom >= scroll_height:
                        break
                    scroll_top = captured_bottom - OVERLAP

                await page.evaluate(
                    "() => { const el = document.querySelector('[data-scroller]'); if (el) el.removeAttribute('data-scroller'); }"
                )

                return _stitch(strips)

            else:
                if scroll_height <= vp_h + 10:
                    return await page.screenshot(type="png")
                logger.info(f"Using body full_page screenshot, scrollHeight={scroll_height}")
                return await page.screenshot(type="png", full_page=True)

        finally:
            # Restore hidden elements
            await page.evaluate("""
                () => {
                    const hidden = document.querySelectorAll('[data-screenshot-hidden]');
                    for (const el of hidden) {
                        const prev = el.getAttribute('data-screenshot-hidden');
                        el.style.display = prev || '';
                        el.removeAttribute('data-screenshot-hidden');
                    }
                }
            """)
