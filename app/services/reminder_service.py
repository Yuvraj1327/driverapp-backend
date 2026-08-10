from __future__ import annotations
import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ReminderStatus
from app.models.reminder import Reminder
from app.repositories.reminder_repository import ReminderRepository
from app.schemas.common import Page
from app.schemas.reminder import ReminderCreate, ReminderUpdate
from app.services.exceptions import NotFoundError


class ReminderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ReminderRepository(db)

    async def create(self, data: ReminderCreate) -> Reminder:
        return await self.repo.create(data.model_dump())

    async def get(self, reminder_id: uuid.UUID) -> Reminder:
        reminder = await self.repo.get(reminder_id)
        if not reminder:
            raise NotFoundError("Reminder", str(reminder_id))
        return reminder

    async def list(
        self, page: int, page_size: int, status: ReminderStatus | None = None
    ) -> Page[Reminder]:
        filters = {"status": status} if status else None
        items, total = await self.repo.list(page=page, page_size=page_size, filters=filters)
        return Page.create(items=items, total=total, page=page, page_size=page_size)

    async def mark_read(self, reminder_id: uuid.UUID) -> Reminder:
        reminder = await self.repo.get(reminder_id)
        if not reminder:
            raise NotFoundError("Reminder", str(reminder_id))
        return await self.repo.update(reminder, {"status": ReminderStatus.READ})

    async def update(self, reminder_id: uuid.UUID, data: ReminderUpdate) -> Reminder:
        reminder = await self.repo.get(reminder_id)
        if not reminder:
            raise NotFoundError("Reminder", str(reminder_id))
        return await self.repo.update(reminder, data.model_dump(exclude_unset=True))

    async def delete(self, reminder_id: uuid.UUID) -> None:
        reminder = await self.repo.get(reminder_id)
        if not reminder:
            raise NotFoundError("Reminder", str(reminder_id))
        await self.repo.delete(reminder)
