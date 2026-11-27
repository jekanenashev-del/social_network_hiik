from typing import Any, Dict, Optional
from app.games.base import GamePlugin
from app.games.registry import register

WIN_LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))

@register
class TicTacToe(GamePlugin):
    slug = "tic-tac-toe"
    name = "Крестики-нолики"
    description = "Классическая игра 3×3"
    min_players = 2
    max_players = 2

    def initial_state(self, players: list[str]) -> Dict[str, Any]:
        return {"board": [None] * 9, "marks": {players[0]: "X", players[1]: "O"}, "players": players}

    def validate_move(self, state, player_id, move) -> None:
        cell = move.get("cell")
        if not isinstance(cell, int) or not (0 <= cell <= 8): raise ValueError("Клетка должна быть от 0 до 8")
        if state["board"][cell] is not None: raise ValueError("Клетка уже занята")

    def apply_move(self, state, player_id, move) -> Dict[str, Any]:
        new_state = {"board": list(state["board"]), "marks": dict(state["marks"]), "players": list(state["players"])}
        new_state["board"][move["cell"]] = state["marks"][player_id]
        return new_state

    def check_finished(self, state) -> Dict[str, Any]:
        board = state["board"]
        for a, b, c in WIN_LINES:
            if board[a] and board[a] == board[b] == board[c]:
                return {"finished": True, "winner_id": next(p for p, m in state["marks"].items() if m == board[a]), "is_draw": False}
        if all(c is not None for c in board): return {"finished": True, "winner_id": None, "is_draw": True}
        return {"finished": False, "winner_id": None, "is_draw": False}

    def next_player(self, state, players, current) -> str: return players[1] if current == players[0] else players[0]
    def render_state(self, state, viewer_id: Optional[str] = None) -> Dict[str, Any]: return {"board": state["board"]}