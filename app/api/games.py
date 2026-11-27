from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.games import Game, GameSession  # <--- ДОБАВЛЕН GameSession
from app.schemas.games import GameOut, MoveIn, SessionOut, SessionStartIn
from app.services import game_service
from app.services.game_service import GameError

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

@router.get("", response_model=list[GameOut])
def list_games(db: Session = Depends(get_db)):
    return db.query(Game).all()

@router.get("/catalog", response_class=HTMLResponse)
def catalog_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("games/catalog.html", {"request": request, "games": db.query(Game).all()})

@router.get("/{slug}", response_model=GameOut)
def get_game(slug: str, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.slug == slug).one_or_none()
    if not game:
        raise HTTPException(404, "Игра не найдена")
    return game

@router.post("/{slug}/start", response_model=SessionOut)
def start_game(slug: str, body: SessionStartIn, db: Session = Depends(get_db)):
    try:
        return game_service.create_session(db, slug, body.player1_id, body.player2_id)
    except GameError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/sessions/{session_id}", response_class=HTMLResponse)
def session_page(session_id: str, request: Request, db: Session = Depends(get_db)):
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "Партия не найдена")
    return templates.TemplateResponse("games/session.html", {
        "request": request,
        "session": session,
        "state": game_service.get_state(db, session_id)
    })

@router.post("/sessions/{session_id}/move", response_model=SessionOut)
def make_move(session_id: str, body: MoveIn, db: Session = Depends(get_db)):
    return game_service.make_move(db, session_id, body.player_id, body.move)

@router.get("/sessions/{session_id}/state")
def get_state(session_id: str, viewer_id: str | None = None, db: Session = Depends(get_db)):
    return game_service.get_state(db, session_id, viewer_id)