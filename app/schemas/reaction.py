from pydantic import BaseModel

class ReactionCreate(BaseModel):
    # Черновик: согласовать post_id/kind с владельцем Reactions.
    post_id: int
    kind: str = "like"
