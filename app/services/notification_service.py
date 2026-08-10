from __future__ import annotations
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.notification_repository import NotificationRepository
from app.schemas.common import Page
from app.services.exceptions import NotFoundError, PermissionDeniedError


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = NotificationRepository(db)

    async def list_for_user(
        self, user_id: uuid.UUID, page: int, page_size: int, unread_only: bool = False
    ) -> Page[Notification]:
        items, total = await self.repo.list_for_user(user_id, page, page_size, unread_only)
        return Page.create(items=items, total=total, page=page, page_size=page_size)

    async def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification:
        notification = await self.repo.get(notification_id)
        if not notification:
            raise NotFoundError("Notification", str(notification_id))
        if notification.user_id != user_id:
            raise PermissionDeniedError("This notification does not belong to you")
        return await self.repo.update(notification, {"is_read": True})
