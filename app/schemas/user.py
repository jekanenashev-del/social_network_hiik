from pydantic import BaseModel, ConfigDict

class UserRead(BaseModel):
    id: int
    username: str
    email: str  # По плану — только для /auth/me.
    role: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
