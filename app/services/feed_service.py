"""Сервис ленты (модуль 10).

Собственных таблиц нет и в БД сервис не ходит: только через сервисы
модулей 6 (связи), 9 (посты) и 12 (статистика). Зависимости передаются
в конструктор, поэтому сервис тестируется на фейках.
"""
from __future__ import annotations

from typing import Any, Protocol, Sequence

from app.schemas.feed import FeedMode, FeedPage, FeedQuery


class RelationsService(Protocol):  # модуль 6
    def get_friend_ids(self, user_id: int) -> Sequence[int]: ...
    def get_subscription_ids(self, user_id: int) -> Sequence[int]: ...


class PostsService(Protocol):  # модуль 9
    def list_by_authors(
        self, ids: Sequence[int], page: int, per_page: int, sort: str
    ) -> Any: ...  # объект со .items и .total

    def list_all(self, page: int, per_page: int, sort: str) -> Any: ...


class StatsService(Protocol):  # модуль 12
    def stats_for_many(
        self, target_type: str, ids: Sequence[int], viewer_id: int | None
    ) -> dict[int, Any]: ...


class FeedService:
    def __init__(
        self,
        *,
        relations: RelationsService,
        posts: PostsService,
        stats: StatsService,
    ) -> None:
        self._relations = relations
        self._posts = posts
        self._stats = stats

    @staticmethod
    def resolve_mode(viewer: Any | None, requested: FeedMode | None) -> FeedMode:
        """Гость всегда получает global; авторизованный по умолчанию — подписки."""
        if viewer is None:
            return FeedMode.GLOBAL
        return requested or FeedMode.SUBSCRIPTIONS

    def get_feed(self, viewer: Any | None, query: FeedQuery) -> FeedPage:
        mode = self.resolve_mode(viewer, query.mode)
        sort = query.sort.value

        if mode is FeedMode.SUBSCRIPTIONS:
            # viewer здесь точно не None (см. resolve_mode)
            author_ids = {viewer.id}
            author_ids.update(self._relations.get_friend_ids(viewer.id))
            author_ids.update(self._relations.get_subscription_ids(viewer.id))
            result = self._posts.list_by_authors(
                sorted(author_ids), page=query.page, per_page=query.per_page, sort=sort
            )
        else:
            result = self._posts.list_all(
                page=query.page, per_page=query.per_page, sort=sort
            )

        items = list(result.items)
        total = int(result.total)

        # Один батч на всю страницу — без N+1.
        stats = (
            self._stats.stats_for_many(
                target_type="post",
                ids=[p.id for p in items],
                viewer_id=viewer.id if viewer else None,
            )
            if items
            else {}
        )

        return FeedPage(
            mode=mode,
            sort=query.sort,
            page=query.page,
            per_page=query.per_page,
            total=total,
            items=items,
            stats=stats,
            has_next=query.page * query.per_page < total,
            has_prev=query.page > 1,
            show_login_banner=viewer is None,
        )
