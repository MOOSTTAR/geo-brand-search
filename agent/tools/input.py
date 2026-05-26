import asyncio
from typing import Any

from agent.tools.base import BaseTool
from agent.harness.context import AgentContext
from agent.harness.errors import ElementNotFoundError, TimeoutExceededError
from agent.harness.logger import get_logger

logger = get_logger(__name__)

# Chat input selectors — if any of these are visible, user is logged in
INPUT_SELECTORS = [
    "textarea",
    "[role='textbox']",
    "[contenteditable='true']",
    "#chat-input",
    ".chat-input textarea",
    "[class*='chat'] textarea",
    "[class*='input'] textarea",
    "[class*='message'] textarea",
    "[class*='editor'] textarea",
    "[class*='editor'] [contenteditable]",
    "textarea[placeholder]",
]

# Login page indicators
LOGIN_PAGE_SELECTORS = [
    "text=登录",
    "text=手机号",
    "text=微信登录",
    "text=扫码",
    "[class*='login']",
    "[class*='Login']",
    "input[type='tel']",
    "input[placeholder*='手机']",
    "input[placeholder*='邮箱']",
    "canvas[class*='qr']",
    "[class*='qrcode']",
]

SUBMIT_SELECTORS = [
    "button[aria-label*='发送']",
    "button[type='submit']",
    "[class*='send']",
    "[class*='submit']",
    "button:has(svg)",
    "button.send-btn",
]


class InputTool(BaseTool):
    name = "input"
    description = "Type text into chat input, submit, and wait for response"

    async def execute(self, ctx: AgentContext, params: dict[str, Any]) -> dict[str, Any]:
        if not ctx.page:
            return {"success": False, "error": "No page available"}

        action = params.get("action", "type_and_submit")

        if action == "type_and_submit":
            return await self._type_and_submit(ctx, params)
        elif action == "wait_for_response":
            return await self._wait_for_response(ctx)
        elif action == "extract_response":
            return await self._extract_response(ctx)
        elif action == "wait_for_login":
            return await self._wait_for_login(ctx)
        else:
            return {"success": False, "error": f"Unknown input action: {action}"}

    async def _check_login_status(self, page) -> tuple[bool, bool]:
        """Returns (is_logged_in, is_login_page)."""
        for selector in INPUT_SELECTORS:
            try:
                el = await page.query_selector(selector)
                if el and await el.is_visible():
                    return True, False
            except Exception:
                continue

        for selector in LOGIN_PAGE_SELECTORS:
            try:
                el = await page.query_selector(selector)
                if el and await el.is_visible():
                    return False, True
            except Exception:
                continue

        return False, False

    async def _enable_deep_think(self, page) -> bool:
        """Ensure '深度思考' toggle is enabled.
        Finds the toggle button by text content and small size (not chat-area labels).
        """
        try:
            result = await page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('[role="button"]');
                    for (const btn of btns) {
                        const text = (btn.textContent || '').trim();
                        if (!text.includes('深度思考')) continue;
                        const r = btn.getBoundingClientRect();
                        // Toggle button is small, skip large containers
                        if (r.width > 200 || r.height > 60) continue;
                        const pressed = btn.getAttribute('aria-pressed');
                        const cls = String(btn.className || '');
                        const isSelected = pressed === 'true' || cls.includes('--selected');
                        return {
                            found: true,
                            selected: isSelected,
                            x: Math.round(r.left + r.width / 2),
                            y: Math.round(r.top + r.height / 2),
                        };
                    }
                    return {found: false};
                }
            """)

            if not result.get("found"):
                logger.info("Deep Think toggle not found on page")
                return False

            if result["selected"]:
                logger.info("Deep Think already enabled")
                return True

            logger.info(f"Enabling Deep Think at ({result['x']},{result['y']})")
            await page.mouse.click(result["x"], result["y"])
            await asyncio.sleep(0.5)

            # Verify it's now enabled
            verify = await page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('[role="button"]');
                    for (const btn of btns) {
                        const text = (btn.textContent || '').trim();
                        if (text.includes('深度思考')) {
                            const pressed = btn.getAttribute('aria-pressed');
                            const cls = String(btn.className || '');
                            return pressed === 'true' || cls.includes('--selected');
                        }
                    }
                    return false;
                }
            """)
            logger.info(f"Deep Think enabled: {verify}")
            return verify
        except Exception as e:
            logger.warning(f"Failed to enable Deep Think: {e}")
            return False

    async def _wait_for_login(self, ctx: AgentContext) -> dict[str, Any]:
        page = ctx.page
        logger.info("Waiting for user to log in to DeepSeek...")

        print("", flush=True)
        print("=" * 60, flush=True)
        print("  请在浏览器中登录 DeepSeek 账号", flush=True)
        print("  登录完成后 Agent 将自动继续...", flush=True)
        print("=" * 60, flush=True)

        poll_interval = 3
        waited = 0
        last_report_time = 0
        last_status = None

        while True:
            is_logged_in, is_login_page = await self._check_login_status(page)

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

    async def _type_and_submit(self, ctx: AgentContext, params: dict[str, Any]) -> dict[str, Any]:
        text = params.get("text", "")
        if not text:
            return {"success": False, "error": "No text to input"}

        page = ctx.page

        # Small delay for page to settle after login
        await asyncio.sleep(1)

        # Step 0: Enable Deep Think before typing
        await self._enable_deep_think(page)

        # Try to find input field
        input_el = None
        found_selector = None
        for selector in INPUT_SELECTORS:
            try:
                el = await page.wait_for_selector(selector, timeout=5000)
                if el and await el.is_visible():
                    input_el = el
                    found_selector = selector
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

        # Submit via page.keyboard.press Enter (DeepSeek listens at page level)
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
        """Wait for DeepSeek response to complete, then extract response text.

        Uses document.body.innerText (visible rendered text only) to track growth.
        Captures baseline at start, requires meaningful growth beyond baseline,
        then waits for text to stabilize for 6 consecutive polls with no loading indicators.
        After completion, extracts the assistant's response text.
        """
        page = ctx.page
        max_wait = 180
        poll_interval = 1.5
        stable_threshold = 6
        min_elapsed = 15
        min_growth = 80

        logger.info("Waiting for DeepSeek response to complete...")

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


    async def _extract_response(self, ctx: AgentContext) -> dict[str, Any]:
        """Scroll page, expand panels, then extract thinking + answer separately."""
        page = ctx.page
        await _scroll_full_page(page)
        await _expand_thinking_panel(page)
        await asyncio.sleep(0.5)

        thinking_text, answer_text, answer_html = await _extract_response_parts(page)

        # Combine for backwards compatibility
        parts = []
        if thinking_text:
            parts.append(thinking_text)
        if answer_text:
            parts.append(answer_text)
        full_text = "\n\n".join(parts)

        return {
            "success": True,
            "response_text": full_text,
            "thinking_text": thinking_text,
            "answer_text": answer_text,
            "answer_html": answer_html,
        }


async def _scroll_full_page(page) -> None:
    """Scroll through the entire page to trigger lazy rendering of all content."""
    try:
        await page.evaluate("""
            async () => {
                const scrollStep = window.innerHeight * 0.7;
                const delay = ms => new Promise(r => setTimeout(r, ms));
                const totalHeight = Math.max(
                    document.body.scrollHeight,
                    document.documentElement.scrollHeight
                );
                for (let y = 0; y < totalHeight; y += scrollStep) {
                    window.scrollTo(0, y);
                    await delay(150);
                }
                // Scroll back to top
                window.scrollTo(0, 0);
                await delay(300);
            }
        """)
        logger.info("Scrolled through full page for text extraction")
    except Exception as e:
        logger.warning(f"Scroll full page failed: {e}")


async def _expand_thinking_panel(page) -> None:
    """Expand DeepSeek's '已思考' / thinking panel if collapsed."""
    try:
        expanded = await page.evaluate("""
            () => {
                // DeepSeek thinking toggle — look for elements containing '已思考' or '思考过程'
                const all = document.querySelectorAll('[class*="thinking"], [class*="reasoning"], ' +
                    '[class*="expand"], [class*="collapse"], [class*="toggle"], ' +
                    'details, summary, [aria-expanded]');
                for (const el of all) {
                    const text = (el.textContent || '').trim();
                    if (text.includes('已思考') || text.includes('思考') || text.includes('用时')) {
                        // Click to expand if it's a toggle/button
                        if (el.tagName === 'SUMMARY' || el.tagName === 'BUTTON' ||
                            el.getAttribute('aria-expanded') === 'false' ||
                            el.getAttribute('role') === 'button') {
                            el.click();
                            return 'clicked: ' + text.substring(0, 30);
                        }
                        // Try clicking parent
                        const parent = el.closest('summary, button, [role="button"], [aria-expanded]');
                        if (parent) {
                            parent.click();
                            return 'clicked parent: ' + text.substring(0, 30);
                        }
                    }
                }
                // Fallback: click any element whose textContent starts with '已思考'
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
                let node;
                while (node = walker.nextNode()) {
                    if (node.children.length === 0 && node.textContent &&
                        node.textContent.trim().startsWith('已思考')) {
                        const clickable = node.closest('[role="button"], button, summary, [aria-expanded]') || node;
                        clickable.click();
                        return 'fallback click: ' + node.textContent.trim().substring(0, 30);
                    }
                }
                return 'not found';
            }
        """)
        logger.info(f"Expand thinking panel: {expanded}")
    except Exception as e:
        logger.warning(f"Failed to expand thinking panel: {e}")


async def _extract_response_parts(page) -> tuple[str, str, str]:
    """Extract thinking text and answer text from DeepSeek's DOM.

    DeepSeek's DOM structure:
      - Thinking section: element with style "--collapsible-area-title-height"
      - Answer section:  element with class "ds-markdown"
    """
    try:
        result = await page.evaluate("""
            () => {
                // --- Answer: last .ds-markdown.ds-assistant-message-main-content ---
                let answerText = '';
                let answerHtml = '';
                const allMarkdown = document.querySelectorAll('.ds-markdown.ds-assistant-message-main-content');
                const markdownEl = allMarkdown.length > 0 ? allMarkdown[allMarkdown.length - 1] : null;
                if (markdownEl) {
                    const clone = markdownEl.cloneNode(true);

                    // Remove code block banners (copy/download/run buttons)
                    const banners = clone.querySelectorAll('.md-code-block-banner-wrap');
                    banners.forEach(b => b.remove());

                    // Remove citation elements
                    const removals = clone.querySelectorAll(
                        'sup, sub, ' +
                        '[class*="reference"], [class*="citation"], [class*="source"], ' +
                        'svg, ._9bc997d, .ds-focus-ring'
                    );
                    removals.forEach(el => el.remove());

                    // Clean span wrappers: unwrap spans with no class or empty class
                    const spans = clone.querySelectorAll('span');
                    spans.forEach(s => {
                        const cls = s.className || '';
                        if (typeof cls !== 'string' || cls.trim() === '') {
                            // Plain span — replace with its children
                            while (s.firstChild) {
                                s.parentNode.insertBefore(s.firstChild, s);
                            }
                            s.remove();
                        }
                    });

                    answerHtml = clone.innerHTML.trim();
                    // Also get plain text for backwards compatibility
                    answerText = (clone.textContent || '').trim();
                    answerText = answerText.replace(/reference\\s*:\\s*\\d+/gi, '');
                    answerText = answerText.replace(/\\s*-\\s*$/gm, '');
                    answerText = answerText.replace(/\\n{3,}/g, '\\n\\n');
                }

                // --- Thinking: element with --collapsible-area-title-height ---
                let thinkingText = '';
                const all = document.querySelectorAll('[style*="--collapsible-area-title-height"]');
                for (const el of all) {
                    const text = (el.textContent || '').trim();
                    if (text.includes('已思考') || text.includes('用时')) {
                        thinkingText = text;
                        break;
                    }
                }

                return { thinking: thinkingText, answer: answerText, answerHtml: answerHtml };
            }
        """)

        thinking = (result.get("thinking") or "").strip() if result else ""
        answer = (result.get("answer") or "").strip() if result else ""
        answer_html = (result.get("answerHtml") or "").strip() if result else ""

        logger.info(f"Extracted thinking={len(thinking)} chars, answer={len(answer)} chars, html={len(answer_html)} chars")
        return thinking, answer, answer_html

    except Exception as e:
        logger.warning(f"Failed to extract response parts: {e}")
        return "", ""
