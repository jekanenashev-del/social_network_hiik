from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserRead

class NotificationRead(BaseModel):
    id: int
    kind: str
    actor: UserRead | None = None
    target_type: str | None = None
    target_id: int | None = None
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
