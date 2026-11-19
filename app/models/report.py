# Сделал Васильев модерация пока сам нечего не понимаю но я пытался
from datetime import datetime
from sqlalchemy import (
    BigInteger, String, Text, DateTime, ForeignKey,
    CheckConstraint, UniqueConstraint, Index, func
)
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base  # Импортируйте ваш базовый класс декларативных моделей


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    target_type: Mapped[str] = mapped_column(String(16), nullable=False)
    target_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    resolved_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("target_type IN ('post', 'comment', 'user')", name="ck_report_target_type"),
        CheckConstraint("status IN ('open', 'resolved', 'rejected')", name="ck_report_status"),
        UniqueConstraint("reporter_id", "target_type", "target_id", name="uq_report_user_target"),
        Index("ix_reports_status_created_at", "status", created_at.desc()),
        Index("ix_reports_target", "target_type", "target_id"),
    )
