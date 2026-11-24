from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Общий базовый класс SQLAlchemy-моделей."""


# Импорты моделей нужны Alembic, чтобы он видел их таблицы.
# Сохраняй этот блок и дополняй при добавлении новых моделей.
from app.models.user import User, Profile  # noqa: E402, F401
from app.models.social import Friendship, Subscription  # noqa: E402, F401
from app.models.content import Post, Comment, Reaction, Media, PostMedia  # noqa: E402, F401
from app.models.messaging import Message, Notification  # noqa: E402, F401
from app.models.community import Group, GroupMember  # noqa: E402, F401
from app.models.moderation import Report, ModerationLog  # noqa: E402, F401
from app.models.games import Game, GameSession, GameMove, GameInvite  # noqa: E402, F401
