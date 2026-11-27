import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from app.database import Base

def _uuid() -> str: return str(uuid.uuid4())

class Game(Base):
    __tablename__ = "games"
    id = Column(String, primary_key=True, default=_uuid)
    slug = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    min_players = Column(Integer, default=2)
    max_players = Column(Integer, default=2)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class GameSession(Base):
    __tablename__ = "game_sessions"
    id = Column(String, primary_key=True, default=_uuid)
    game_id = Column(String, ForeignKey("games.id"), nullable=False, index=True)
    player1_id = Column(String, nullable=True)
    player2_id = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False, index=True)
    state = Column(JSON, default=dict, nullable=False)
    current_turn = Column(String, nullable=True)
    winner_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    game = relationship("Game")
    moves = relationship("GameMove", back_populates="session", order_by="GameMove.move_number")

class GameMove(Base):
    __tablename__ = "game_moves"
    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("game_sessions.id"), nullable=False, index=True)
    player_id = Column(String, nullable=True)
    move_number = Column(Integer, nullable=False)
    move_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    session = relationship("GameSession", back_populates="moves")
    __table_args__ = (Index("ix_game_moves_session_move", "session_id", "move_number"),)