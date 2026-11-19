# Сделал Васильев модерация пока сам нечего не понимаю но я пытался
import json
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report
from app.models.moderation_log import ModerationLog
from app.models.user import User  # Из модуля 3/4
# Импорты из соседних модулей согласно ТЗ:
from app.services.notification_service import notify  # Модуль 8
from app.services.post_service import PostService  # Модуль 9
from app.services.comment_service import CommentService  # Модуль 11


class ModerationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _log_action(
            self,
            admin_id: int,
            action: str,
            target_type: str | None = None,
            target_id: int | None = None,
            details: dict | None = None,
    ) -> None:
        log_entry = ModerationLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=json.dumps(details, ensure_ascii=False) if details else None,
        )
        self.db.add(log_entry)

    async def create_report(
            self,
            reporter: User,
            target_type: str,
            target_id: int,
            reason: str,
            comment: str | None = None,
    ) -> Report:
        report = Report(
            reporter_id=reporter.id,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            comment=comment,
        )
        self.db.add(report)
        try:
            await self.db.commit()
            await self.db.refresh(report)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Вы уже отправляли жалобу на этот объект.",
            )
        return report

    async def list_reports(self, status_filter: str | None = None, page: int = 1, limit: int = 20):
        query = select(Report).order_by(Report.created_at.desc())
        if status_filter:
            query = query.where(Report.status == status_filter)

        offset = (page - 1) * limit
        result = await self.db.execute(query.offset(offset).limit(limit))
        return result.scalars().all()

    async def resolve_report(
            self,
            report_id: int,
            admin: User,
            resolution: str,  # 'resolved' или 'rejected'
            delete_content: bool = False,
    ) -> Report:
        report = await self.db.get(Report, report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Жалоба не найдена")

        if report.status != "open":
            raise HTTPException(status_code=400, detail="Жалоба уже закрыта")

        report.status = resolution
        report.resolved_by = admin.id
        report.resolved_at = datetime.now(timezone.utc)

        author_id = None

        # Если нужно удалить контент и получить его автора для уведомления
        if resolution == "resolved" and delete_content:
            if report.target_type == "post":
                author_id = await PostService.get_author(self.db, report.target_id)
                await PostService.soft_delete(self.db, report.target_id, by_admin=True)
                await self._log_action(admin.id, "delete_post", "post", report.target_id)
            elif report.target_type == "comment":
                author_id = await CommentService.get_author(self.db, report.target_id)
                await CommentService.soft_delete(self.db, report.target_id, by_admin=True)
                await self._log_action(admin.id, "delete_comment", "comment", report.target_id)

        await self._log_action(
            admin_id=admin.id,
            action=f"{resolution}_report",
            target_type="report",
            target_id=report.id,
            details={"target_type": report.target_type, "target_id": report.target_id},
        )

        await self.db.commit()
        await self.db.refresh(report)

        # Уведомление автора через модуль 8
        if author_id:
            await notify(
                user_id=author_id,
                kind="moderation",
                payload={"report_id": report.id, "resolution": resolution},
            )

        return report

    async def block_user(self, user_id: int, admin: User) -> User:
        if user_id == admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя заблокировать самого себя.",
            )

        user = await self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        user.is_active = False
        await self._log_action(admin.id, "block_user", "user", user.id)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def unblock_user(self, user_id: int, admin: User) -> User:
        user = await self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        user.is_active = True
        await self._log_action(admin.id, "unblock_user", "user", user.id)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def promote_to_admin(self, user_id: int, admin: User) -> User:
        user = await self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        user.role = "admin"  # Адаптируйте под способ хранения ролей в Модуле 4
        await self._log_action(admin.id, "promote_to_admin", "user", user.id)
        await self.db.commit()
        await self.db.refresh(user)
        return user
