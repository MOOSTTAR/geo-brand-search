"""豆包 (Doubao) chat platform integration."""

import asyncio
import json

from agent.platforms.base import Platform
from agent.harness.logger import get_logger

logger = get_logger(__name__)


class DoubaoPlatform(Platform):
    key = "doubao"
    name = "豆包"
    url = "https://www.doubao.com/chat/"

    @property
    def input_selectors(self) -> list[str]:
        return [
            "textarea",
            "[role='textbox']",
            "[contenteditable='true']",
            "textarea[placeholder]",
            "[class*='input'] textarea",
            "[class*='editor'] textarea",
            "[class*='editor'] [contenteditable]",
            "[class*='chat'] textarea",
            "[class*='chat'] [contenteditable]",
        ]

    @property
    def login_indicators(self) -> list[str]:
        return [
            "text=登录",
            "text=手机号",
            "text=验证码",
            "text=扫码",
            "[class*='login']",
            "[class*='Login']",
            "input[type='tel']",
            "input[placeholder*='手机']",
        ]

    # ── extraction ─────────────────────────────────────────────────────

    async def extract_response(self, page) -> dict[str, str | None]:
        await _scroll_full_page(page)
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
        """Try to collapse 豆包 sidebar by clicking the sidebar toggle button."""
        try:
            result = await page.evaluate("""
                () => {
                    // 豆包 sidebar toggle — look for the button with the grid/dashboard icon
                    // The user showed this button has data-dbx-name="button" and SVG icon
                    const btns = document.querySelectorAll('[data-dbx-name="button"]');
                    for (const btn of btns) {
                        const svg = btn.querySelector('svg');
                        if (!svg) continue;
                        const r = btn.getBoundingClientRect();
                        if (r.width > 0 && r.height > 0 && r.width < 60 && r.height < 60 && r.left < 80) {
                            return {
                                found: true,
                                x: Math.round(r.left + r.width / 2),
                                y: Math.round(r.top + r.height / 2),
                            };
                        }
                    }
                    // Fallback: any small button on the left edge
                    const allBtns = document.querySelectorAll('button, [role="button"]');
                    for (const btn of allBtns) {
                        const r = btn.getBoundingClientRect();
                        if (r.width > 0 && r.height > 0 && r.width < 60 && r.height < 60 && r.left < 80 && r.top < 80) {
                            const svg = btn.querySelector('svg');
                            if (svg) {
                                return {
                                    found: true,
                                    x: Math.round(r.left + r.width / 2),
                                    y: Math.round(r.top + r.height / 2),
                                };
                            }
                        }
                    }
                    return {found: false};
                }
            """)

            if result.get("found"):
                logger.info(f"Clicking 豆包 sidebar toggle at ({result['x']},{result['y']})")
                await page.mouse.click(result["x"], result["y"])
                await asyncio.sleep(1.0)
                return True

            logger.info("豆包 sidebar toggle not found")
            return False
        except Exception as e:
            logger.warning(f"Failed to collapse 豆包 sidebar: {e}")
            return False


# ── helper functions ───────────────────────────────────────────────────

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


async def _extract_response_parts(page) -> tuple[str, str, str]:
    """Extract thinking text and answer text from 豆包's DOM.

    豆包 renders AI responses in a conversation thread. The last assistant
    message contains the answer. Thinking/reasoning may be in a collapsible
    section above the final answer.
    """
    try:
        result = await page.evaluate("""
            () => {
                let answerText = '';
                let answerHtml = '';
                let thinkingText = '';

                // Strategy 1: find the last assistant message bubble
                // 豆包 uses dbx- prefixed classes; try generic selectors first
                const messages = document.querySelectorAll(
                    '[class*="message"], [class*="bubble"], [class*="response"], ' +
                    '[class*="answer"], [class*="assistant"], [class*="bot"], ' +
                    '[class*="content"]'
                );

                // Filter to visible elements with substantial text content
                const candidates = [];
                for (const el of messages) {
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) continue;
                    const text = (el.textContent || '').trim();
                    if (text.length > 100) {
                        candidates.push({ el, text, bottom: r.bottom });
                    }
                }

                // Sort by vertical position, take the bottom-most (last response)
                candidates.sort((a, b) => b.bottom - a.bottom);

                if (candidates.length > 0) {
                    const last = candidates[candidates.length - 1];
                    const clone = last.el.cloneNode(true);

                    // Remove code action bars, buttons, icons
                    const removals = clone.querySelectorAll(
                        'button, [role="button"], svg, img, ' +
                        '[class*="toolbar"], [class*="action"], [class*="copy"], ' +
                        '[class*="banner"], [class*="badge"]'
                    );
                    removals.forEach(el => el.remove());

                    answerHtml = clone.innerHTML.trim();
                    answerText = (clone.textContent || '').trim();
                    answerText = answerText.replace(/\\n{3,}/g, '\\n\\n');
                }

                // Strategy 2: fallback — grab all visible text in main content area
                if (!answerText) {
                    // Try to find the main chat area and get all its text
                    const mainArea = document.querySelector(
                        '[class*="chat"], [class*="conversation"], [class*="thread"], ' +
                        'main, [role="main"], [class*="main"]'
                    );
                    if (mainArea) {
                        const clone = mainArea.cloneNode(true);
                        const removals = clone.querySelectorAll(
                            'button, [role="button"], svg, img, ' +
                            '[class*="toolbar"], [class*="action"], [class*="copy"], ' +
                            '[class*="banner"], [class*="badge"], nav, header, ' +
                            '[class*="sidebar"], [class*="side"]'
                        );
                        removals.forEach(el => el.remove());
                        answerText = (clone.textContent || '').trim();
                        answerHtml = clone.innerHTML.trim();
                    }
                }

                // Strategy 3: last resort — grab body text excluding nav/footer
                if (!answerText) {
                    const body = document.body.cloneNode(true);
                    const removals = body.querySelectorAll(
                        'nav, header, footer, button, [role="button"], svg, img, ' +
                        '[class*="sidebar"], [class*="side"], [class*="toolbar"], ' +
                        '[class*="input"], [class*="textarea"]'
                    );
                    removals.forEach(el => el.remove());
                    answerText = (body.textContent || '').trim();
                    answerHtml = body.innerHTML.trim();
                }

                // Try to extract thinking/reasoning
                const thinkingEls = document.querySelectorAll(
                    '[class*="thinking"], [class*="reasoning"], [class*="thought"], ' +
                    '[class*="chain"], [class*="process"], [class*="深度"], ' +
                    '[class*="思考"], [class*="推理"]'
                );
                for (const el of thinkingEls) {
                    const text = (el.textContent || '').trim();
                    if (text.length > 50) {
                        thinkingText = text;
                        break;
                    }
                }

                return {
                    thinking: thinkingText,
                    answer: answerText,
                    answerHtml: answerHtml,
                };
            }
        """)

        thinking = (result.get("thinking") or "").strip() if result else ""
        answer = (result.get("answer") or "").strip() if result else ""
        answer_html = (result.get("answerHtml") or "").strip() if result else ""

        logger.info(f"豆包 extracted thinking={len(thinking)} chars, answer={len(answer)} chars, html={len(answer_html)} chars")
        return thinking, answer, answer_html

    except Exception as e:
        logger.warning(f"Failed to extract 豆包 response parts: {e}")
        return "", "", ""


async def _extract_sources(page) -> str:
    """Extract citation sources from 豆包's response.

    豆包 may show sources as:
    - Clickable citation numbers in the answer text
    - A sources/references section at the bottom of the response
    - A side panel that opens when clicking a source button
    """
    try:
        baseline = await page.evaluate(
            "() => document.querySelectorAll('a[href*=\"http\"]').length"
        )

        # Try to find and click a source/reference button
        clicked = await page.evaluate("""
            () => {
                // Look for source count indicators like "N 个来源" or "N sources"
                const all = document.querySelectorAll('[class], button, span, div');
                for (const el of all) {
                    const text = (el.textContent || '').trim();
                    const m = text.match(/^(\\d+)\\s*(个来源|个网页|个参考|条来源|sources?|references?)/i);
                    if (m && parseInt(m[1]) > 0) {
                        const r = el.getBoundingClientRect();
                        if (r.width > 0 && r.height > 0 && r.width < 300) {
                            el.click();
                            return {method: 'text', text: text};
                        }
                    }
                }
                // Look for source-related elements
                const srcEls = document.querySelectorAll(
                    '[class*="source"], [class*="citation"], [class*="reference"], ' +
                    '[class*="search"], [class*="result"]'
                );
                for (const el of srcEls) {
                    const r = el.getBoundingClientRect();
                    const text = (el.textContent || '').trim();
                    if (r.width > 0 && r.height > 0 && text.length > 0 && text.length < 50) {
                        el.click();
                        return {method: 'class', text: text};
                    }
                }
                return false;
            }
        """)

        if not clicked:
            logger.info("No source button found on 豆包, trying inline extraction")
            # Try extracting inline sources (links within the answer)
            sources = await page.evaluate("""
                () => {
                    const items = [];
                    const seen = new Set();

                    // Find all external links that look like citations
                    const links = document.querySelectorAll('a[href*="http"]');
                    for (const a of links) {
                        const href = a.getAttribute('href') || '';
                        if (!href || href === '#' || seen.has(href)) continue;
                        if (href.includes('doubao.com')) continue;

                        const r = a.getBoundingClientRect();
                        if (r.width === 0 || r.height === 0) continue;

                        // Only include links in the response area (not nav/sidebar)
                        const inSidebar = a.closest('[class*="sidebar"], [class*="side"], nav, header');
                        if (inSidebar) continue;

                        seen.add(href);

                        const text = (a.textContent || '').trim();
                        items.push({
                            logo: '',
                            site_name: '',
                            title: text || href,
                            url: href,
                            date: '',
                            snippet: '',
                            cite: '',
                        });

                        if (items.length >= 200) break;
                    }
                    return items;
                }
            """)

            if sources:
                logger.info(f"Extracted {len(sources)} inline source links from 豆包")
                return json.dumps(sources, ensure_ascii=False)
            return ""

        await asyncio.sleep(2.5)

        # Extract sources from opened panel
        sources = await page.evaluate("""
            () => {
                const items = [];
                const seen = new Set();

                // Find a right-side panel with links
                let panel = null;
                const candidates = document.querySelectorAll(
                    '[class*="drawer"], [class*="panel"], [class*="overlay"], ' +
                    '[class*="modal"], [class*="popup"], [class*="sheet"], ' +
                    '[class*="sidebar"], [class*="side"]'
                );
                for (const c of candidates) {
                    const r = c.getBoundingClientRect();
                    if (r.width > 200 && r.height > 200) {
                        const links = c.querySelectorAll('a[href*="http"]');
                        if (links.length >= 3) {
                            panel = c;
                            break;
                        }
                    }
                }

                const searchRoot = panel || document.body;
                const links = searchRoot.querySelectorAll('a[href*="http"]');
                for (const a of links) {
                    const href = a.getAttribute('href') || '';
                    if (!href || href === '#' || seen.has(href)) continue;
                    if (href.includes('doubao.com')) continue;

                    const r = a.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) continue;

                    seen.add(href);

                    const rawText = (a.textContent || '').trim();
                    let siteName = '', title = rawText;

                    // Try to split site name from title
                    const parts = rawText.split(/\\s{2,}/);
                    if (parts.length >= 2) {
                        siteName = parts[0];
                        title = parts.slice(1).join(' ');
                    }

                    items.push({
                        logo: '',
                        site_name: siteName,
                        title: title,
                        url: href,
                        date: '',
                        snippet: '',
                        cite: '',
                    });

                    if (items.length >= 200) break;
                }
                return items;
            }
        """)

        # Try to close the panel
        try:
            await page.evaluate("""
                () => {
                    const all = document.querySelectorAll('[class]');
                    for (const el of all) {
                        const text = (el.textContent || '').trim();
                        if (/^\\d+\\s*(个来源|个网页|sources?)$/i.test(text)) {
                            el.click();
                            return;
                        }
                    }
                }
            """)
        except Exception:
            pass
        await asyncio.sleep(0.5)

        if not sources:
            logger.info("No source items found in 豆包 panel")
            return ""

        logger.info(f"Extracted {len(sources)} source items from 豆包")
        return json.dumps(sources, ensure_ascii=False)

    except Exception as e:
        logger.warning(f"豆包 source extraction failed: {e}")
        return ""
