from pydantic import BaseModel, Field
from typing import Optional


class TaskCreateRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


class TaskResponse(BaseModel):
    id: str
    query: str
    status: str
    progress: int
    current_step: Optional[str] = None
    screenshot_path: Optional[str] = None
    response_text: Optional[str] = None
    thinking_text: Optional[str] = None
    answer_text: Optional[str] = None
    answer_html: Optional[str] = None
    ranking_table: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None

    model_config = {"from_attributes": True}
