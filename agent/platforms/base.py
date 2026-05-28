"""Abstract base class for AI chat platform integrations."""

from abc import ABC, abstractmethod
from typing import Any


class Platform(ABC):
    """Each subclass defines the browser-automation recipe for one AI chat platform."""

    @property
    @abstractmethod
    def key(self) -> str:
        """Short unique key, e.g. 'deepseek', 'doubao'."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name, e.g. 'DeepSeek', '豆包'."""
        ...

    @property
    @abstractmethod
    def url(self) -> str:
        """Chat page URL to navigate to."""
        ...

    # ── selectors ──────────────────────────────────────────────────────

    @property
    def input_selectors(self) -> list[str]:
        """CSS selectors to find the chat input element (tried in order)."""
        return [
            "textarea",
            "[role='textbox']",
            "[contenteditable='true']",
            "textarea[placeholder]",
        ]

    @property
    def login_indicators(self) -> list[str]:
        """Selectors that signal a login page (not logged in)."""
        return [
            "text=登录",
            "text=手机号",
            "text=微信登录",
            "[class*='login']",
            "[class*='Login']",
        ]

    # ── hooks ──────────────────────────────────────────────────────────

    async def pre_submit(self, page) -> None:
        """Called after the chat input is found, before typing the query."""
        pass

    # ── extraction ─────────────────────────────────────────────────────

    @abstractmethod
    async def extract_response(self, page) -> dict[str, str | None]:
        """Extract thinking_text, answer_text, answer_html from the page.

        Returns a dict with keys: thinking_text, answer_text, answer_html.
        """
        ...

    @abstractmethod
    async def extract_sources(self, page) -> str:
        """Extract citation sources as a JSON string.

        Returns empty string if no sources found.
        """
        ...

    # ── sidebar ────────────────────────────────────────────────────────

    async def collapse_sidebar(self, page) -> bool:
        """Try to collapse the sidebar. Return True on success."""
        return False
