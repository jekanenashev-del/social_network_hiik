from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.games import registry
from app.models.games import Game, GameMove, GameSession


class GameError(Exception):
    pass


def _get_game(db: Session, slug: str) -> Game:
    game = db.query(Game).filter(Game.slug == slug).one_or_none()
    if game is None:
        raise GameError(f"Игра '{slug}' не найдена")
    return game


def create_session(db: Session, slug: str, player1_id: str, player2_id: str) -> GameSession:
    if player1_id == player2_id:
        raise GameError("Нельзя создать партию с самим собой")
    game = _get_game(db, slug)
    plugin = registry.get(slug)
    players = [player1_id, player2_id]
    session = GameSession(
        game_id=game.id,
        player1_id=player1_id,
        player2_id=player2_id,
        status="active",
        state=plugin.initial_state(players),
        current_turn=players[0]
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str) -> GameSession:
    session = db.query(GameSession).filter(GameSession.id == session_id).one_or_none()
    if session is None:
        raise GameError("Партия не найдена")
    return session


def make_move(db: Session, session_id: str, player_id: str, move: Dict[str, Any]) -> GameSession:
    session = get_session(db, session_id)

    # ПРОВЕРКА СТАТУСА
    if session.status != "active":
        raise GameError(f"Партия в статусе '{session.status}', ход невозможен")

    # ПРОВЕРКА ОЧЕРЕДИ (то, чего не хватало!)
    if player_id != session.current_turn:
        raise GameError("Сейчас не ваш ход")

    game = db.query(Game).filter(Game.id == session.game_id).one()
    plugin = registry.get(game.slug)

    try:
        plugin.validate_move(session.state, player_id, move)
    except ValueError as exc:
        raise GameError(str(exc)) from exc

    new_state = plugin.apply_move(session.state, player_id, move)

    # Сохраняем ход в историю с правильным номером
    last = db.query(GameMove).filter(GameMove.session_id == session.id).order_by(GameMove.move_number.desc()).first()
    move_number = (last.move_number + 1) if last else 1
    db.add(GameMove(session_id=session.id, player_id=player_id, move_number=move_number, move_data=move))

    session.state = new_state
    finished = plugin.check_finished(new_state)

    if finished["finished"]:
        session.status = "finished"
        session.winner_id = finished["winner_id"]
        session.current_turn = None
    else:
        players = [p for p in (session.player1_id, session.player2_id) if p]
        session.current_turn = plugin.next_player(new_state, players, player_id)

    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session


def get_state(db: Session, session_id: str, viewer_id: Optional[str] = None) -> Dict[str, Any]:
    session = get_session(db, session_id)
    game = db.query(Game).filter(Game.id == session.game_id).one()
    plugin = registry.get(game.slug)
    return {
        "session_id": session.id,
        "status": session.status,
        "current_turn": session.current_turn,
        "winner_id": session.winner_id,
        "state": plugin.render_state(session.state, viewer_id)
    }