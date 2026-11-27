from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class GamePlugin(ABC):
    slug: str
    name: str
    description: str = ""
    min_players: int = 2
    max_players: int = 2

    @abstractmethod
    def initial_state(self, players: list[str]) -> Dict[str, Any]: ...
    @abstractmethod
    def validate_move(self, state: Dict[str, Any], player_id: str, move: Dict[str, Any]) -> None: ...
    @abstractmethod
    def apply_move(self, state: Dict[str, Any], player_id: str, move: Dict[str, Any]) -> Dict[str, Any]: ...
    @abstractmethod
    def check_finished(self, state: Dict[str, Any]) -> Dict[str, Any]: ...
    @abstractmethod
    def next_player(self, state: Dict[str, Any], players: list[str], current: str) -> str: ...
    @abstractmethod
    def render_state(self, state: Dict[str, Any], viewer_id: Optional[str] = None) -> Dict[str, Any]: ...