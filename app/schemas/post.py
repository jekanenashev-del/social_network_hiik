from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserRead

class PostRead(BaseModel):
    id: int
    author: UserRead
    content: str
    created_at: datetime
    likes_count: int = 0
    comments_count: int = 0
    liked_by_me: bool = False
    model_config = ConfigDict(from_attributes=True)

class PostCreate(BaseModel):
    # Черновик: точные поля в плане не заданы — согласовать с владельцем Posts.
    content: str
