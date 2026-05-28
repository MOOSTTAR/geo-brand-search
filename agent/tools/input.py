import asyncio
from typing import Any

from agent.tools.base import BaseTool
from agent.harness.context import AgentContext
from agent.platforms import get_platform
from agent.platforms.base import Platform
from agent.harness.logger import get_logger

logger = get_logger(__name__)


class InputTool(BaseTool):
    name = "input"
    description = "Type text into chat input, submit, and wait for response"

    async def execute(self, ctx: AgentContext, params: dict[str, Any]) -> dict[str, Any]:
        if not ctx.page:
            return {"success": False, "error": "No page available"}

        platform_key = params.get("platform", "deepseek")
        platform = get_platform(platform_key)
        action = params.get("action", "type_and_submit")

        if action == "type_and_submit":
            return await self._type_and_submit(ctx, params, platform)
        elif action == "wait_for_response":
            return await self._wait_for_response(ctx)
        elif action == "extract_response":
            return await self._extract_response(ctx, platform)
        elif action == "wait_for_login":
            return await self._wait_for_login(ctx, platform)
        else:
            return {"success": False, "error": f"Unknown input action: {action}"}

    async def _check_login_status(self, page, platform: Platform) -> tuple[bool, bool]:
        """Returns (is_logged_in, is_login_page)."""
        for selector in platform.input_selectors:
            try:
                el = await page.query_selector(selector)
                if el and await el.is_visible():
                    return True, False
            except Exception:
                continue

        for selector in platform.login_indicators:
            try:
                el = await page.query_selector(selector)
                if el and await el.is_visible():
                    return False, True
            except Exception:
                continue

        return False, False

    async def _wait_for_login(self, ctx: AgentContext, platform: Platform) -> dict[str, Any]:
        page = ctx.page
        logger.info(f"Waiting for user to log in to {platform.name}...")

        print("", flush=True)
        print("=" * 60, flush=True)
        print(f"  请在浏览器中登录 {platform.name} 账号", flush=True)
        print("  登录完成后 Agent 将自动继续...", flush=True)
        print("=" * 60, flush=True)

        poll_interval = 3
        waited = 0
        last_report_time = 0
        last_status = None

        while True:
            is_logged_in, is_login_page = await self._check_login_status(page, platform)

            if is_logged_in:
                logger.info(f"Login detected! Chat input found after {waited}s")
                await asyncio.sleep(1)
                return {"success": True, "message": "已登录，开始搜索"}

            if is_login_page:
                current_status = "login_page"
            else:
                current_status = "unknown"

            if current_status != last_status or (waited - last_report_time >= 15):
                last_status = current_status
                last_report_time = waited
                if is_login_page:
                    logger.info(f"[{waited}s] 检测到登录页面，等待用户登录...")
                else:
                    logger.info(f"[{waited}s] 等待页面加载，正在检测登录状态...")

            await asyncio.sleep(poll_interval)
            waited += poll_interval

    async def _type_and_submit(self, ctx: AgentContext, params: dict[str, Any], platform: Platform) -> dict[str, Any]:
        text = params.get("text", "")
        if not text:
            return {"success": False, "error": "No text to input"}

        page = ctx.page

        # Small delay for page to settle after login
        await asyncio.sleep(1)

        # Platform-specific pre-submit hook (e.g. DeepSeek "深度思考" toggle)
        await platform.pre_submit(page)

        # Try to find input field using platform selectors
        input_el = None
        for selector in platform.input_selectors:
            try:
                el = await page.wait_for_selector(selector, timeout=5000)
                if el and await el.is_visible():
                    input_el = el
                    logger.info(f"Found input with selector: {selector}")
                    break
            except Exception:
                continue

        if not input_el:
            url = page.url
            title = await page.title()
            logger.error(f"Cannot find input. URL={url}, Title={title}")
            try:
                html_snippet = await page.evaluate(
                    "() => document.body.innerText.substring(0, 500)"
                )
                logger.error(f"Page text: {html_snippet}")
            except Exception:
                pass
            return {"success": False, "error": f"Could not find input field. Page: {title}"}

        # Click and type
        try:
            await input_el.click()
            await asyncio.sleep(0.3)
            await input_el.fill(text)
            await asyncio.sleep(0.3)
        except Exception as e:
            try:
                await input_el.click()
                await asyncio.sleep(0.2)
                await page.keyboard.type(text, delay=50)
            except Exception as e2:
                return {"success": False, "error": f"Failed to type text: {e2}"}

        # Submit via page.keyboard.press Enter
        submitted = False
        try:
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)
            submitted = True
            logger.info("Submitted via page.keyboard Enter")
        except Exception as e:
            logger.warning(f"page.keyboard Enter failed: {e}")

        # Fallback: element.press Enter
        if not submitted:
            try:
                await input_el.press("Enter")
                await asyncio.sleep(1)
                submitted = True
                logger.info("Submitted via element Enter")
            except Exception as e:
                logger.warning(f"element Enter failed: {e}")

        # Fallback: JS click any visible button
        if not submitted:
            try:
                clicked = await page.evaluate("""
                    () => {
                        const btns = document.querySelectorAll('button');
                        for (const btn of btns) {
                            const r = btn.getBoundingClientRect();
                            if (r.width === 0 || r.height === 0) continue;
                            const info = (btn.textContent||'')+(btn.getAttribute('aria-label')||'')+(btn.className||'');
                            if (/send|submit|发送|submit/i.test(info)) { btn.click(); return true; }
                        }
                        for (const btn of btns) {
                            const r = btn.getBoundingClientRect();
                            if (r.width > 0 && r.height > 0 && r.bottom > 0) { btn.click(); return true; }
                        }
                        return false;
                    }
                """)
                if clicked:
                    await asyncio.sleep(1)
                    submitted = True
                    logger.info("Submitted via JS button click")
            except Exception as e:
                logger.warning(f"JS button click failed: {e}")

        if not submitted:
            return {"success": False, "error": "All submit methods failed"}

        return {"success": True, "message": "Text submitted"}

    async def _wait_for_response(self, ctx: AgentContext) -> dict[str, Any]:
        """Wait for AI response to complete, then return.

        Uses document.body.innerText to track text growth.
        """
        page = ctx.page
        max_wait = 180
        poll_interval = 1.5
        stable_threshold = 6
        min_elapsed = 15
        min_growth = 80

        logger.info("Waiting for AI response to complete...")

        await asyncio.sleep(2)

        try:
            baseline_text = await page.evaluate("() => document.body.innerText || ''")
        except Exception:
            baseline_text = ""
        baseline_len = len(baseline_text)
        logger.info(f"Baseline visible text: {baseline_len} chars")

        last_len = baseline_len
        stable_count = 0
        waited = 0
        peak_len = baseline_len

        while waited < max_wait:
            try:
                result = await page.evaluate("""
                    () => {
                        const text = document.body.innerText || '';
                        return { text: text, len: text.length };
                    }
                """)

                text_len = result["len"]

                indicators = await page.evaluate("""
                    () => {
                        const stopBtn = document.querySelector(
                            '[class*="stop"], [aria-label*="stop"], [aria-label*="停止"], ' +
                            '[class*="pause"], [class*="cancel"], [class*="abort"]'
                        );
                        let stopVisible = false;
                        if (stopBtn) {
                            const r = stopBtn.getBoundingClientRect();
                            stopVisible = r.width > 0 && r.height > 0;
                        }

                        const loaders = document.querySelectorAll(
                            '[class*="loading"], [class*="streaming"], [class*="generating"], ' +
                            '[class*="thinking"], [class*="pending"], [class*="typing"], ' +
                            '[class*="dot"], [class*="pulse"], [class*="spin"], [class*="waiting"], ' +
                            '[class*="loader"], [class*="spinner"], ' +
                            'svg[class*="animate"], [class*="animate-spin"]'
                        );
                        let loadingVisible = false;
                        for (const el of loaders) {
                            const r = el.getBoundingClientRect();
                            if (r.width > 0 && r.height > 0) {
                                const s = window.getComputedStyle(el);
                                if (s.display !== 'none' && s.visibility !== 'hidden') {
                                    loadingVisible = true;
                                    break;
                                }
                            }
                        }
                        return { stopVisible, loadingVisible };
                    }
                """)

                loading = indicators["loadingVisible"]
                stop_visible = indicators["stopVisible"]
                growth = text_len - baseline_len

                if text_len > peak_len:
                    peak_len = text_len

                if text_len != last_len:
                    delta = text_len - last_len
                    logger.info(
                        f"[{waited:.0f}s] visible text: {last_len} -> {text_len} "
                        f"(+{delta}), growth={growth}, loading={loading}, stop={stop_visible}"
                    )

                grown_enough = growth >= min_growth
                elapsed_enough = waited >= min_elapsed
                text_stable = text_len == last_len

                if elapsed_enough and grown_enough and text_stable and not stop_visible:
                    stable_count += 1
                    if stable_count >= stable_threshold:
                        logger.info(
                            f"Response complete: {text_len} chars (growth={growth}), "
                            f"stable {stable_count} polls, {waited:.0f}s elapsed"
                        )
                        return {
                            "success": True,
                            "message": "Response generation complete",
                        }
                elif text_len != last_len:
                    stable_count = 0
                    last_len = text_len

            except Exception as e:
                logger.warning(f"Response check failed: {e}")

            await asyncio.sleep(poll_interval)
            waited += poll_interval

        logger.info(f"Wait timeout ({max_wait}s), peak growth={peak_len - baseline_len} chars")
        return {"success": True, "message": "Wait timeout reached, proceeding anyway"}

    async def _extract_response(self, ctx: AgentContext, platform: Platform) -> dict[str, Any]:
        """Delegate response extraction to the platform implementation."""
        page = ctx.page

        # Extract response parts via platform
        extracted = await platform.extract_response(page)

        # Extract sources via platform
        sources_json = await platform.extract_sources(page)

        # Combine thinking + answer for backwards-compatible response_text
        parts = []
        if extracted.get("thinking_text"):
            parts.append(extracted["thinking_text"])
        if extracted.get("answer_text"):
            parts.append(extracted["answer_text"])
        full_text = "\n\n".join(parts)

        return {
            "success": True,
            "response_text": full_text,
            "thinking_text": extracted.get("thinking_text", ""),
            "answer_text": extracted.get("answer_text", ""),
            "answer_html": extracted.get("answer_html", ""),
            "sources_json": sources_json,
        }
