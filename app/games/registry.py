from typing import Dict, Type
from sqlalchemy.orm import Session
from app.games.base import GamePlugin
from app.models.games import Game

_REGISTRY: Dict[str, Type[GamePlugin]] = {}

def register(plugin_cls: Type[GamePlugin]) -> Type[GamePlugin]:
    _REGISTRY[plugin_cls.slug] = plugin_cls
    return plugin_cls

def get(slug: str) -> GamePlugin:
    if slug not in _REGISTRY: raise KeyError(f"Игра '{slug}' не зарегистрирована")
    return _REGISTRY[slug]()

def sync_with_db(db: Session) -> None:
    for slug, cls in _REGISTRY.items():
        row = db.query(Game).filter(Game.slug == slug).one_or_none()
        if row is None:
            db.add(Game(slug=slug, name=cls.name, description=cls.description, min_players=cls.min_players, max_players=cls.max_players, is_active=1))
    db.commit()