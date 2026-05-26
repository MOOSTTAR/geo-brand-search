from pydantic import BaseModel
from typing import Optional, Any


class WsMessage(BaseModel):
    type: str
    data: dict[str, Any]
