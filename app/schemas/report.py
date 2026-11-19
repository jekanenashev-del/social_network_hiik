# Сделал Васильев модерация пока сам нечего не понимаю но я пытался
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class ReportCreate(BaseModel):
    target_type: Literal["post", "comment", "user"]
    target_id: int
    reason: Literal["spam", "abuse", "other"]
    comment: str | None = Field(default=None, max_length=1000)


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reporter_id: int
    target_type: str
    target_id: int
    reason: str
    comment: str | None
    status: str
    resolved_by: int | None
    resolved_at: datetime | None
    created_at: datetime
