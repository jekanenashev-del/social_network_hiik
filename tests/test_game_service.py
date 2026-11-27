import pytest
from app.services import game_service
from app.services.game_service import GameError

def test_create_session_active(db_session):
    s = game_service.create_session(db_session, "tic-tac-toe", "u1", "u2")
    assert s.status == "active" and s.current_turn == "u1"

def test_move_changes_turn(db_session):
    s = game_service.create_session(db_session, "tic-tac-toe", "u1", "u2")
    s = game_service.make_move(db_session, s.id, "u1", {"cell": 0})
    assert s.state["board"][0] == "X" and s.current_turn == "u2"

def test_wrong_turn_rejected(db_session):
    s = game_service.create_session(db_session, "tic-tac-toe", "u1", "u2")
    with pytest.raises(GameError): game_service.make_move(db_session, s.id, "u2", {"cell": 0})