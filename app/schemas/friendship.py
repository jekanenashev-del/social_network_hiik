from datetime import datetime
from pydantic import BaseModel, ConfigDict

class FriendshipRead(BaseModel):
    # Черновик: согласовать поля с владельцем Friendship.
    id: int
    requester_id: int
    addressee_id: int
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
