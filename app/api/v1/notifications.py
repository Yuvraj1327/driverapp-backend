"""
Notification endpoints: list current user's notifications, mark read.
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import pagination_params
from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.common import Page
from app.schemas.notification import NotificationRead
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=Page[NotificationRead])
async def list_my_notifications(
    pagination: tuple[int, int] = Depends(pagination_params),
    unread_only: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Page[NotificationRead]:
    page, page_size = pagination
    service = NotificationService(db)
    result = await service.list_for_user(current_user.id, page, page_size, unread_only)
    return Page[NotificationRead](
        items=[NotificationRead.model_validate(n) for n in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )


@router.post("/{notification_id}/mark-read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationRead:
    service = NotificationService(db)
    notification = await service.mark_read(notification_id, current_user.id)
    return NotificationRead.model_validate(notification)
