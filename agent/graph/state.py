from typing import TypedDict


class AgentGraphState(TypedDict, total=False):
    task_id: str
    query: str
    headless: bool
    platform: str
    progress: int
    current_step: str
    screenshot_path: str | None
    response_text: str | None
    thinking_text: str | None
    answer_text: str | None
    answer_html: str | None
    sources_json: str | None
    error: str | None
