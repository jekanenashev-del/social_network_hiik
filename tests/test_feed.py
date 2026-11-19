"""Тесты модуля 10 «Лента».

Юнит-тесты работают на фейках (без БД). Интеграционные тесты внизу требуют
реальных модулей 3/9/12 и фикстур БД проекта — они помечены skip.
"""
from dataclasses import dataclass
from types import SimpleNamespace

import shutil
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

from app.api import feed as feed_api
from app.schemas.feed import FeedMode, FeedQuery, FeedSort
from app.services.feed_service import FeedService


# --------------------------------------------------------------------- фейки
@dataclass
class Post:
    id: int
    author_id: int


class FakeRelations:
    def __init__(self, friends=(), subs=()):
        self.friends, self.subs = list(friends), list(subs)

    def get_friend_ids(self, user_id):
        return self.friends

    def get_subscription_ids(self, user_id):
        return self.subs


class FakePosts:
    """Хранит посты от новых к старым; считает вызовы."""

    def __init__(self, posts):
        self.posts = sorted(posts, key=lambda p: -p.id)
        self.calls = []

    def _page(self, rows, page, per_page):
        start = (page - 1) * per_page
        return SimpleNamespace(items=rows[start:start + per_page], total=len(rows))

    def list_by_authors(self, ids, page, per_page, sort):
        self.calls.append(("authors", list(ids), page, per_page, sort))
        rows = [p for p in self.posts if p.author_id in set(ids)]
        return self._page(rows, page, per_page)

    def list_all(self, page, per_page, sort):
        self.calls.append(("all", page, per_page, sort))
        return self._page(self.posts, page, per_page)


class FakeStats:
    def __init__(self):
        self.calls = []

    def stats_for_many(self, target_type, ids, viewer_id):
        self.calls.append((target_type, list(ids), viewer_id))
        return {i: {"likes": 0} for i in ids}


def make_service(posts, friends=(), subs=()):
    p, s = FakePosts(posts), FakeStats()
    return FeedService(relations=FakeRelations(friends, subs), posts=p, stats=s), p, s


USER = SimpleNamespace(id=1)
POSTS = [Post(id=i, author_id=a) for i, a in enumerate([1, 2, 3, 4, 2, 1, 5, 3], start=1)]


# ------------------------------------------------------------- режим и гость
def test_guest_gets_global_and_banner():
    svc, posts, _ = make_service(POSTS)
    page = svc.get_feed(None, FeedQuery())
    assert page.mode is FeedMode.GLOBAL
    assert page.show_login_banner is True
    assert posts.calls[0][0] == "all"


def test_guest_requesting_subscriptions_is_switched_to_global():
    svc, posts, _ = make_service(POSTS)
    page = svc.get_feed(None, FeedQuery(mode=FeedMode.SUBSCRIPTIONS))
    assert page.mode is FeedMode.GLOBAL
    assert [c[0] for c in posts.calls] == ["all"]


def test_authorized_default_is_subscriptions_without_banner():
    svc, posts, _ = make_service(POSTS, friends=[2], subs=[3])
    page = svc.get_feed(USER, FeedQuery())
    assert page.mode is FeedMode.SUBSCRIPTIONS
    assert page.show_login_banner is False
    assert {p.author_id for p in page.items} <= {1, 2, 3}


def test_subscriptions_include_self_friends_and_subs_deduplicated():
    svc, posts, _ = make_service(POSTS, friends=[2, 3], subs=[3, 4])
    svc.get_feed(USER, FeedQuery(mode=FeedMode.SUBSCRIPTIONS))
    _, ids, *_ = posts.calls[0]
    assert ids == [1, 2, 3, 4]


def test_subscriptions_with_no_relations_still_include_own_posts():
    svc, posts, _ = make_service(POSTS)
    page = svc.get_feed(USER, FeedQuery())
    assert {p.author_id for p in page.items} == {1}


def test_authorized_can_choose_global():
    svc, posts, _ = make_service(POSTS, friends=[2])
    page = svc.get_feed(USER, FeedQuery(mode=FeedMode.GLOBAL))
    assert page.mode is FeedMode.GLOBAL
    assert posts.calls[0][0] == "all"
    assert page.total == len(POSTS)


# ---------------------------------------------------------- сортировка/стата
def test_sort_and_paging_params_are_forwarded():
    svc, posts, _ = make_service(POSTS)
    svc.get_feed(None, FeedQuery(sort=FeedSort.POPULAR, page=2, per_page=3))
    assert posts.calls[0] == ("all", 2, 3, "popular")


def test_stats_fetched_in_single_batch_for_page_ids():
    svc, _, stats = make_service(POSTS)
    page = svc.get_feed(USER, FeedQuery(mode=FeedMode.GLOBAL, per_page=3))
    assert len(stats.calls) == 1
    assert stats.calls[0] == ("post", [p.id for p in page.items], USER.id)
    assert set(page.stats) == {p.id for p in page.items}


def test_stats_viewer_id_is_none_for_guest():
    svc, _, stats = make_service(POSTS)
    svc.get_feed(None, FeedQuery())
    assert stats.calls[0][2] is None


def test_empty_feed_skips_stats_call():
    svc, _, stats = make_service([])
    page = svc.get_feed(USER, FeedQuery())
    assert page.items == [] and page.total == 0
    assert stats.calls == []
    assert not page.has_next and not page.has_prev


# ----------------------------------------------------------------- пагинация
def test_walking_all_pages_has_no_gaps_or_duplicates():
    svc, _, _ = make_service(POSTS)
    seen, page_no = [], 1
    while True:
        page = svc.get_feed(None, FeedQuery(page=page_no, per_page=3))
        seen += [p.id for p in page.items]
        if not page.has_next:
            break
        page_no += 1
    assert sorted(seen) == sorted(p.id for p in POSTS)
    assert len(seen) == len(set(seen))


def test_has_prev_and_has_next_flags():
    svc, _, _ = make_service(POSTS)  # 8 постов
    assert svc.get_feed(None, FeedQuery(page=1, per_page=4)).has_next is True
    last = svc.get_feed(None, FeedQuery(page=2, per_page=4))
    assert last.has_next is False and last.has_prev is True


# ------------------------------------------------------------- разбор запроса
@pytest.mark.parametrize(
    "raw, expected",
    [
        (dict(mode="foo", sort="bar", page="abc", per_page="-5"),
         (None, FeedSort.NEW, 1, 1)),
        (dict(mode="global", sort="popular", page="0", per_page="9999"),
         (FeedMode.GLOBAL, FeedSort.POPULAR, 1, 50)),
        (dict(), (None, FeedSort.NEW, 1, 20)),
    ],
)
def test_query_parsing_never_fails(raw, expected):
    q = FeedQuery.from_params(**raw)
    assert (q.mode, q.sort, q.page, q.per_page) == expected


# ---------------------------------------------------------------- HTTP-слой
@pytest.fixture(autouse=True)
def stub_templates(tmp_path, monkeypatch):
    """base.html и post_card.html принадлежат другим модулям — подменяем
    заглушками, реальным остаётся только feed/index.html."""
    (tmp_path / "partials").mkdir()
    (tmp_path / "feed").mkdir()
    (tmp_path / "base.html").write_text(
        "{% block content %}{% endblock %}", encoding="utf-8")
    (tmp_path / "partials" / "post_card.html").write_text(
        "<div class='post'>{{ post.id }}</div>", encoding="utf-8")
    real = Path(feed_api.TEMPLATES_DIR) / "feed" / "index.html"
    shutil.copy(real, tmp_path / "feed" / "index.html")
    monkeypatch.setattr(feed_api, "templates", Jinja2Templates(directory=str(tmp_path)))


def make_client(viewer, service):
    app = FastAPI()
    app.include_router(feed_api.router)
    app.dependency_overrides[feed_api.get_current_user_optional] = lambda: viewer
    app.dependency_overrides[feed_api.get_feed_service] = lambda: service
    return TestClient(app)


def test_root_and_feed_render_same_page_for_guest():
    svc, _, _ = make_service(POSTS)
    client = make_client(None, svc)
    for url in ("/", "/feed"):
        r = client.get(url)
        assert r.status_code == 200
        assert "Войдите, чтобы видеть свои подписки" in r.text


def test_url_params_reach_service_and_garbage_does_not_422():
    svc, posts, _ = make_service(POSTS)
    client = make_client(USER, svc)
    assert client.get("/feed?mode=global&sort=popular&page=2").status_code == 200
    assert posts.calls[-1][0] == "all" and posts.calls[-1][-1] == "popular"
    assert client.get("/feed?mode=zzz&page=-1&sort=").status_code == 200


def test_empty_feed_shows_placeholder():
    svc, _, _ = make_service([])
    r = make_client(USER, svc).get("/")
    assert "Пока нет постов. Подпишитесь на кого-нибудь" in r.text


# ------------------------------------------- интеграционные (нужны модули 3/9/12)
INTEGRATION = pytest.mark.skip(reason="нужны реальные модули 3/9/12 и фикстуры БД проекта")


@INTEGRATION
def test_deleted_users_and_is_deleted_posts_are_hidden():
    """Создать пост с is_deleted=True и пост удалённого автора → их нет в ленте."""


@INTEGRATION
def test_popular_orders_by_likes_plus_comments_x2():
    """A: 3 лайка (score 3); B: 1 лайк + 2 коммента (score 5) → B выше A."""


@INTEGRATION
def test_no_n_plus_one():
    """Считать запросы (event 'before_cursor_execute') на seed ≥ 50 постов:
    1 запрос постов + 1 батч реакций + 1 батч комментариев."""


@INTEGRATION
def test_home_page_under_one_second_on_seed():
    """≥ 50 постов, GET / < 1 сек."""
