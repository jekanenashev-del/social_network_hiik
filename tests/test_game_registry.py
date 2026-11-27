from app.games import registry
def test_registry():
    assert registry.get("tic-tac-toe").slug == "tic-tac-toe"