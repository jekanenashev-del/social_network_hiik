from typing import Any, Dict, Optional
from pydantic import BaseModel

class GameOut(BaseModel):
    slug: str; name: str; description: str; min_players: int; max_players: int
    class Config: from_attributes = True

class SessionStartIn(BaseModel):
    player1_id: str; player2_id: str

class SessionOut(BaseModel):
    id: str; game_id: str; status: str; current_turn: Optional[str]; winner_id: Optional[str]; state: Dict[str, Any]
    class Config: from_attributes = True

class MoveIn(BaseModel):
    player_id: str; move: Dict[str, Any]