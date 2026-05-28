"""DeepSeek chat platform integration."""

import asyncio
import json

from agent.platforms.base import Platform
from agent.harness.logger import get_logger

logger = get_logger(__name__)


class DeepSeekPlatform(Platform):
    key = "deepseek"
    name = "DeepSeek"
    url = "https://chat.deepseek.com"

    @property
    def input_selectors(self) -> list[str]:
        return [
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

    @property
    def login_indicators(self) -> list[str]:
        return [
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

    # ── pre-submit hook ────────────────────────────────────────────────

    async def pre_submit(self, page) -> None:
        """Enable DeepSeek's '深度思考' (Deep Think) toggle before typing."""
        try:
            result = await page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('[role="button"]');
                    for (const btn of btns) {
                        const text = (btn.textContent || '').trim();
                        if (!text.includes('深度思考')) continue;
                        const r = btn.getBoundingClientRect();
                        if (r.width > 200 || r.height > 60) continue;
                        const pressed = btn.getAttribute('aria-pressed');
                        const cls = String(btn.className || '');
                        const isSelected = pressed === 'true' || cls.includes('--selected');
                        return { found: true, selected: isSelected,
                                 x: Math.round(r.left + r.width / 2),
                                 y: Math.round(r.top + r.height / 2) };
                    }
                    return {found: false};
                }
            """)

            if not result.get("found"):
                logger.info("Deep Think toggle not found on page")
                return

            if result["selected"]:
                logger.info("Deep Think already enabled")
                return

            logger.info(f"Enabling Deep Think at ({result['x']},{result['y']})")
            await page.mouse.click(result["x"], result["y"])
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"Failed to enable Deep Think: {e}")

    # ── extraction ─────────────────────────────────────────────────────

    async def extract_response(self, page) -> dict[str, str | None]:
        await _scroll_full_page(page)
        await _expand_thinking_panel(page)
        await asyncio.sleep(0.5)

        thinking_text, answer_text, answer_html = await _extract_response_parts(page)
        return {
            "thinking_text": thinking_text or "",
            "answer_text": answer_text or "",
            "answer_html": answer_html or "",
        }

    async def extract_sources(self, page) -> str:
        return await _extract_sources(page)

    # ── sidebar ────────────────────────────────────────────────────────

    async def collapse_sidebar(self, page) -> bool:
        """Collapse DeepSeek sidebar by counting icon buttons and clicking the right one."""
        return await _collapse_deepseek_sidebar(page)


# ── helper functions (extracted from input.py / sidebar.py) ──────────────

async def _scroll_full_page(page) -> None:
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
                const all = document.querySelectorAll('[class*="thinking"], [class*="reasoning"], ' +
                    '[class*="expand"], [class*="collapse"], [class*="toggle"], ' +
                    'details, summary, [aria-expanded]');
                for (const el of all) {
                    const text = (el.textContent || '').trim();
                    if (text.includes('已思考') || text.includes('思考') || text.includes('用时')) {
                        if (el.tagName === 'SUMMARY' || el.tagName === 'BUTTON' ||
                            el.getAttribute('aria-expanded') === 'false' ||
                            el.getAttribute('role') === 'button') {
                            el.click();
                            return 'clicked: ' + text.substring(0, 30);
                        }
                        const parent = el.closest('summary, button, [role="button"], [aria-expanded]');
                        if (parent) {
                            parent.click();
                            return 'clicked parent: ' + text.substring(0, 30);
                        }
                    }
                }
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
    """Extract thinking text and answer text from DeepSeek's DOM."""
    try:
        result = await page.evaluate("""
            () => {
                let answerText = '';
                let answerHtml = '';
                const allMarkdown = document.querySelectorAll('.ds-markdown.ds-assistant-message-main-content');
                const markdownEl = allMarkdown.length > 0 ? allMarkdown[allMarkdown.length - 1] : null;
                if (markdownEl) {
                    const clone = markdownEl.cloneNode(true);
                    const banners = clone.querySelectorAll('.md-code-block-banner-wrap');
                    banners.forEach(b => b.remove());
                    const removals = clone.querySelectorAll(
                        'sup, sub, ' +
                        '[class*="reference"], [class*="citation"], [class*="source"], ' +
                        'svg, ._9bc997d, .ds-focus-ring'
                    );
                    removals.forEach(el => el.remove());
                    const spans = clone.querySelectorAll('span');
                    spans.forEach(s => {
                        const cls = s.className || '';
                        if (typeof cls !== 'string' || cls.trim() === '') {
                            while (s.firstChild) {
                                s.parentNode.insertBefore(s.firstChild, s);
                            }
                            s.remove();
                        }
                    });
                    answerHtml = clone.innerHTML.trim();
                    answerText = (clone.textContent || '').trim();
                    answerText = answerText.replace(/reference\\s*:\\s*\\d+/gi, '');
                    answerText = answerText.replace(/\\s*-\\s*$/gm, '');
                    answerText = answerText.replace(/\\n{3,}/g, '\\n\\n');
                }

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
        return "", "", ""


async def _extract_sources(page) -> str:
    """Click source button, extract source list, close panel, return JSON string."""
    try:
        baseline = await page.evaluate(
            "() => document.querySelectorAll('a[href*=\"http\"]').length"
        )

        clicked = await page.evaluate("""
            () => {
                const all = document.querySelectorAll('[class]');
                for (const el of all) {
                    const text = (el.textContent || '').trim();
                    const m = text.match(/^(\\d+)\\s*(个网页|个来源|sources?|source)$/i);
                    if (m && parseInt(m[1]) > 0) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0 && rect.width < 300) {
                            el.click();
                            return {method: 'text', text: text};
                        }
                    }
                }
                const btns = document.querySelectorAll('[class*="source"], [class*="citation"], [class*="reference"]');
                for (const el of btns) {
                    const text = (el.textContent || '').trim();
                    if (text.length > 0 && text.length < 30) {
                        el.click();
                        return {method: 'class', text: text};
                    }
                }
                const mds = document.querySelectorAll('.ds-markdown.ds-assistant-message-main-content');
                if (mds.length > 0) {
                    let sibling = mds[mds.length - 1].nextElementSibling;
                    for (let i = 0; i < 5 && sibling; i++) {
                        const text = (sibling.textContent || '').trim();
                        if (/\\d+\\s*(个网页|个来源|sources?)/i.test(text)) {
                            sibling.click();
                            return {method: 'sibling-scan', text: text};
                        }
                        sibling = sibling.nextElementSibling;
                    }
                    const next = mds[mds.length - 1].nextElementSibling;
                    if (next) {
                        next.click();
                        return {method: 'fallback', text: (next.textContent||'').trim().substring(0, 60)};
                    }
                }
                return false;
            }
        """)
        if not clicked:
            logger.info("No source button found, skipping source extraction")
            return ""

        await asyncio.sleep(2.5)

        after = await page.evaluate(
            "() => document.querySelectorAll('a[href*=\"http\"]').length"
        )
        logger.info(f"Links before={baseline}, after={after}")

        sources = await page.evaluate("""
            () => {
                const items = [];
                const seen = new Set();
                let panel = document.querySelector('.fcd12e6e');
                if (!panel) {
                    const candidates = document.querySelectorAll('[class*="drawer"], [class*="panel"], [class*="scroll"], [class*="overlay"], [class*="modal"]');
                    for (const c of candidates) {
                        const r = c.getBoundingClientRect();
                        if (r.width > 200 && r.height > 300 && r.x > window.innerWidth * 0.5) {
                            const links = c.querySelectorAll('a[href*="http"]');
                            if (links.length >= 5) {
                                panel = c;
                                break;
                            }
                        }
                    }
                }
                let searchRoot = panel || document.body;
                const links = searchRoot.querySelectorAll('a[href*="http"]');
                for (const a of links) {
                    const href = a.getAttribute('href') || '';
                    if (!href || href === '#' || seen.has(href)) continue;
                    const rect = a.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) continue;
                    if (a.closest('.ds-markdown')) continue;
                    if (!panel && rect.x < window.innerWidth * 0.5) continue;
                    seen.add(href);

                    let card = a;
                    for (let i = 0; i < 6; i++) {
                        if (!card.parentElement || card.parentElement === searchRoot) break;
                        const p = card.parentElement;
                        const pRect = p.getBoundingClientRect();
                        if (p.children.length > 8 && pRect.width > 300) break;
                        card = p;
                    }

                    const imgs = card.querySelectorAll('img');
                    let logo = '';
                    for (const img of imgs) {
                        const src = img.getAttribute('src') || '';
                        if (!src) continue;
                        const ir = img.getBoundingClientRect();
                        if (ir.width > 10 && ir.width < 40) { logo = src; break; }
                    }
                    if (!logo && imgs.length > 0) {
                        logo = imgs[0].getAttribute('src') || '';
                    }

                    const rawText = (a.textContent || '').trim();
                    let siteName = '', date = '', cite = '', title = '', snippet = '';

                    const dm = rawText.match(/\\d{4}[\\/-]\\d{1,2}[\\/-]\\d{1,2}/);
                    if (dm) {
                        date = dm[0];
                        const di = dm.index;
                        siteName = rawText.substring(0, di).replace(/^\\d{1,2}\\s*/, '').trim();
                        const after = rawText.substring(di + date.length);
                        let cy = after.match(/^(\\d{1,2})(\\d{4}年)/);
                        if (!cy) cy = after.match(/^(\\d{1,2})(\\d{4}(?!\\d))/);
                        if (cy) {
                            cite = cy[1];
                            title = after.substring(cy[1].length).trim();
                        } else if (/^\\d{4}年/.test(after)) {
                            title = after.trim();
                        } else if (/^\\d{4}(?!\\d)/.test(after)) {
                            title = after.trim();
                        } else {
                            const cm = after.match(/^(\\d{1,2})(?=[^\\d]|$)/);
                            if (cm) {
                                cite = cm[1];
                                title = after.substring(cm[1].length).trim();
                            } else {
                                title = after.trim();
                            }
                        }
                    } else {
                        title = rawText;
                    }

                    siteName = siteName.replace(/^\\d{1,2}\\s*/, '').trim();
                    if (siteName.length > 30) {
                        title = siteName + ' ' + title;
                        siteName = '';
                    }

                    const cardText = (card.textContent || '').trim();
                    if (cardText !== rawText && cardText.length > rawText.length) {
                        snippet = cardText.substring(cardText.indexOf(rawText) + rawText.length).trim();
                    }
                    if (!snippet && title.length > 80) {
                        const breakPt = title.indexOf('。');
                        if (breakPt > 15) {
                            snippet = title.substring(breakPt + 1).trim();
                            title = title.substring(0, breakPt + 1).trim();
                        }
                    }
                    snippet = snippet.substring(0, 200);

                    items.push({
                        logo: logo,
                        site_name: siteName,
                        title: title,
                        url: href,
                        date: date,
                        snippet: snippet,
                        cite: cite,
                    });
                    if (items.length >= 200) break;
                }
                return items;
            }
        """)

        # Close source panel
        await page.evaluate("""
            () => {
                const all = document.querySelectorAll('[class]');
                for (const el of all) {
                    const text = (el.textContent || '').trim();
                    if (/^\\d+\\s*(个网页|个来源|sources?)$/i.test(text)) {
                        el.click();
                        return;
                    }
                }
            }
        """)
        await asyncio.sleep(0.5)

        if not sources:
            logger.info("No source items found in panel")
            return ""

        logger.info(f"Extracted {len(sources)} source items")
        return json.dumps(sources, ensure_ascii=False)

    except Exception as e:
        logger.warning(f"Source extraction failed: {e}")
        try:
            await page.evaluate("""
                () => {
                    const all = document.querySelectorAll('[class]');
                    for (const el of all) {
                        const text = (el.textContent || '').trim();
                        if (/^\\d+\\s*(个网页|个来源|sources?)$/i.test(text)) {
                            el.click();
                            return;
                        }
                    }
                }
            """)
        except Exception:
            pass
        return ""


async def _collapse_deepseek_sidebar(page) -> bool:
    """Collapse DeepSeek sidebar using DOM panel width and icon-button counting."""
    import numpy as np
    from PIL import Image
    import io

    HIGH_VARIANCE_THRESHOLD = 35.0

    def _check_sidebar_visible(image_bytes: bytes) -> tuple[bool, float]:
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
        return await page.evaluate("""
            () => {
                const panel = document.querySelector('.dc04ec1d');
                if (!panel) return -1;
                return Math.round(panel.getBoundingClientRect().width);
            }
        """)

    async def _get_top_icon_buttons(page) -> list[dict]:
        return await page.evaluate("""
            () => {
                const results = [];
                const btns = document.querySelectorAll('[role="button"]');
                for (const btn of btns) {
                    const r = btn.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) continue;
                    if (r.width > 50 || r.height > 50) continue;
                    if (r.top > 80) continue;
                    if (r.left > 300) continue;
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

    await asyncio.sleep(0.5)

    sidebar_width = await _get_sidebar_width(page)
    logger.info(f"Sidebar panel width: {sidebar_width}px")
    if 0 <= sidebar_width < 50:
        logger.info("Sidebar already collapsed (DOM check)")
        return True

    icon_buttons = await _get_top_icon_buttons(page)
    logger.info(f"Top icon buttons found: {len(icon_buttons)}")
    for i, b in enumerate(icon_buttons):
        logger.info(f"  [{i}] ({b['x']},{b['y']}) left={b['left']} top={b['top']} {b['w']}x{b['h']}")

    target_index = None
    if len(icon_buttons) == 2:
        target_index = 1
        logger.info("Detected 2 icon buttons (sidebar expanded), will click 2nd one (collapse)")
    elif len(icon_buttons) == 3:
        logger.info("Detected 3 icon buttons, sidebar may already be collapsed")
        return True
    else:
        logger.info(f"Unexpected number of icon buttons: {len(icon_buttons)}, trying rightmost")
        target_index = len(icon_buttons) - 1

    if target_index is None or target_index >= len(icon_buttons):
        return False

    target = icon_buttons[target_index]
    logger.info(f"Clicking icon button [{target_index}] at ({target['x']},{target['y']})")

    try:
        await page.mouse.click(target["x"], target["y"])
    except Exception as e:
        logger.warning(f"Click failed: {e}")
        return False

    await asyncio.sleep(1.0)

    new_width = await _get_sidebar_width(page)
    logger.info(f"After click: sidebar width={new_width}px (was {sidebar_width}px)")

    if 0 <= new_width < 50:
        logger.info(f"Sidebar collapsed successfully! Width {sidebar_width}px -> {new_width}px")
        return True

    try:
        strip = await _capture_left_strip(page)
        visible, max_std = _check_sidebar_visible(strip)
        logger.info(f"After click pixel check: visible={visible}, max_band_std={max_std:.1f}")
        if not visible:
            logger.info("Sidebar collapsed (pixel confirmed)")
            return True
    except Exception as e:
        logger.warning(f"Pixel verification failed: {e}")

    if len(icon_buttons) == 2:
        other_index = 0
        other = icon_buttons[other_index]
        logger.info(f"First attempt didn't work, trying other button [{other_index}] at ({other['x']},{other['y']})")
        try:
            await page.mouse.click(other["x"], other["y"])
            await asyncio.sleep(1.0)
            new_width2 = await _get_sidebar_width(page)
            if 0 <= new_width2 < 50:
                logger.info(f"Sidebar collapsed on retry! Width {sidebar_width}px -> {new_width2}px")
                return True
        except Exception as e:
            logger.warning(f"Retry click failed: {e}")

    logger.info("Sidebar collapse not confirmed")
    return False
