import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="creating")
    progress = Column(Integer, nullable=False, default=0)
    current_step = Column(String(100), nullable=True)
    screenshot_path = Column(String(255), nullable=True)
    response_text = Column(Text, nullable=True)
    thinking_text = Column(Text, nullable=True)
    answer_text = Column(Text, nullable=True)
    answer_html = Column(Text, nullable=True)
    ranking_table = Column(Text, nullable=True)
    brand_keyword = Column(String(255), nullable=True)
    brand_rank = Column(String(255), nullable=True)
    sources_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(String(30), nullable=False,
                        default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at = Column(String(30), nullable=False,
                        default=lambda: datetime.now(timezone.utc).isoformat())
    completed_at = Column(String(30), nullable=True)
