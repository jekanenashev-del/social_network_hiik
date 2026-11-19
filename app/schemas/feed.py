"""Схемы модуля 10 «Лента»."""
from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 50


class FeedMode(StrEnum):
    SUBSCRIPTIONS = "subscriptions"  # свои + друзья + подписки
    GLOBAL = "global"                # все посты системы


class FeedSort(StrEnum):
    NEW = "new"          # по дате
    POPULAR = "popular"  # лайки + комментарии * 2


def _coerce_enum(enum_cls: type[StrEnum], raw: Any, default: Any) -> Any:
    try:
        return enum_cls(raw)
    except ValueError:
        return default


def _coerce_int(raw: Any, default: int) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


class FeedQuery(BaseModel):
    """Параметры ленты из GET-запроса."""

    mode: FeedMode | None = None  # None = «по умолчанию для этого зрителя»
    sort: FeedSort = FeedSort.NEW
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1, le=MAX_PER_PAGE)

    @classmethod
    def from_params(
        cls,
        mode: str | None = None,
        sort: str | None = None,
        page: str | int | None = None,
        per_page: str | int | None = None,
    ) -> "FeedQuery":
        """Мягкий разбор: мусор в URL не должен ронять главную страницу (422)."""
        return cls(
            mode=_coerce_enum(FeedMode, mode, None),
            sort=_coerce_enum(FeedSort, sort, FeedSort.NEW),
            page=max(1, _coerce_int(page, 1)),
            per_page=min(MAX_PER_PAGE, max(1, _coerce_int(per_page, DEFAULT_PER_PAGE))),
        )


class FeedPage(BaseModel):
    """Одна страница ленты, готовая для рендера."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    mode: FeedMode                      # фактический режим (после авто-переключения)
    sort: FeedSort
    page: int
    per_page: int
    total: int
    items: list[Any]                    # PostRead из модуля 9
    stats: dict[int, Any]               # {post_id: stats} из модуля 12
    has_next: bool
    has_prev: bool
    show_login_banner: bool             # True для гостя
