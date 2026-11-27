from app.services import game_service

def test_win(db_session):
    s = game_service.create_session(db_session, "tic-tac-toe", "u1", "u2")
    for p, c in [("u1", 0), ("u2", 3), ("u1", 1), ("u2", 4), ("u1", 2)]:
        s = game_service.make_move(db_session, s.id, p, {"cell": c})
    assert s.status == "finished" and s.winner_id == "u1"