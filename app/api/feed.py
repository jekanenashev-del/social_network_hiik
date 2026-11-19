"""Эндпоинты ленты (модуль 10): GET / и GET /feed."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.schemas.feed import FeedQuery
from app.services.feed_service import FeedService

# --- ТОЧКА СТЫКОВКИ С ДРУГИМИ МОДУЛЯМИ -------------------------------------
# Пока чужих модулей нет, эти зависимости подменяются заглушками (и в тестах
# переопределяются). Когда модули 4/6/9/12 появятся, поправьте пути импорта и
# УДАЛИТЕ блоки try/except — иначе ошибка подключения будет молча проглочена.
try:
    from app.api.deps import get_current_user_optional, get_db  # модуль 4
except ImportError:  # pragma: no cover
    def get_current_user_optional():
        return None

    def get_db():
        raise RuntimeError("Модуль 4 (get_db) не подключён")
# ---------------------------------------------------------------------------

router = APIRouter(tags=["feed"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "web" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_feed_query(
    mode: str | None = Query(None),
    sort: str | None = Query(None),
    page: str | None = Query(None),
    per_page: str | None = Query(None),
) -> FeedQuery:
    return FeedQuery.from_params(mode, sort, page, per_page)


def get_feed_service(db=Depends(get_db)) -> FeedService:
    # Поправьте пути под интерфейсы Sprint 0:
    from app.services.relations_service import RelationsService  # модуль 6
    from app.services.post_service import PostService            # модуль 9
    from app.services.stats_service import StatsService          # модуль 12

    return FeedService(
        relations=RelationsService(db),
        posts=PostService(db),
        stats=StatsService(db),
    )


@router.get("/", response_class=HTMLResponse)
@router.get("/feed", response_class=HTMLResponse)
def feed_page(
    request: Request,
    viewer=Depends(get_current_user_optional),
    query: FeedQuery = Depends(get_feed_query),
    service: FeedService = Depends(get_feed_service),
):
    feed = service.get_feed(viewer, query)
    return templates.TemplateResponse(
        request, "feed/index.html", {"feed": feed, "current_user": viewer}
    )
