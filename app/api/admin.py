# Сделал Васильев модерация пока сам нечего не понимаю но я пытался
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.report import ReportCreate, ReportOut
from app.services.moderation_service import ModerationService
from app.dependencies.auth import get_current_user, require_role  # Из модуля 4

# Роутер для обычных пользователей (отправка жалоб)
reports_router = APIRouter(prefix="/reports", tags=["Reports"])

# Роутер админ-панели (все эндпоинты защищены require_role('admin'))
admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_role("admin"))],
)


@reports_router.post("", response_model=ReportOut, status_code=201)
async def create_report(
    data: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModerationService(db)
    return await service.create_report(
        reporter=current_user,
        target_type=data.target_type,
        target_id=data.target_id,
        reason=data.reason,
        comment=data.comment,
    )


@admin_router.get("")
async def admin_dashboard(db: AsyncSession = Depends(get_db)):
    # Здесь можно добавить подсчет открытых жалоб, заблокированных юзеров и новых регистраций
    # И вернуть TemplateResponse для Jinja2 или JSON
    return {"status": "ok"}


@admin_router.get("/reports", response_model=list[ReportOut])
async def get_reports_queue(
    status: str | None = Query(default="open", pattern="^(open|resolved|rejected)$"),
    page: int = Query(default=1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    service = ModerationService(db)
    return await service.list_reports(status_filter=status, page=page)


@admin_router.post("/reports/{report_id}/resolve", response_model=ReportOut)
async def resolve_report(
    report_id: int,
    delete_content: bool = False,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    service = ModerationService(db)
    return await service.resolve_report(
        report_id=report_id,
        admin=admin,
        resolution="resolved",
        delete_content=delete_content,
    )


@admin_router.post("/reports/{report_id}/reject", response_model=ReportOut)
async def reject_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    service = ModerationService(db)
    return await service.resolve_report(
        report_id=report_id,
        admin=admin,
        resolution="rejected",
        delete_content=False,
    )


@admin_router.post("/users/{user_id}/block")
async def block_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    service = ModerationService(db)
    await service.block_user(user_id=user_id, admin=admin)
    return {"message": "Пользователь заблокирован"}


@admin_router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    service = ModerationService(db)
    await service.unblock_user(user_id=user_id, admin=admin)
    return {"message": "Пользователь разблокирован"}


@admin_router.post("/users/{user_id}/promote")
async def promote_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    service = ModerationService(db)
    await service.promote_to_admin(user_id=user_id, admin=admin)
    return {"message": "Пользователю назначена роль admin"}
