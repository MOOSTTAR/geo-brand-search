from dataclasses import dataclass, field
from typing import Any
from playwright.async_api import Page, Browser, BrowserContext


@dataclass
class AgentContext:
    """Holds all contextual state for an agent run."""
    task_id: str
    query: str
    browser: Browser | None = None
    context: BrowserContext | None = None
    page: Page | None = None
    screenshot_path: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
