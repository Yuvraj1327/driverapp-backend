from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ReminderStatus
from app.models.reminder import Reminder
from app.repositories.base import BaseRepository


class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self, db: AsyncSession):
        super().__init__(Reminder, db)

    async def list_due_before(self, before_date: date, status: ReminderStatus | None = None):
        stmt = select(Reminder).where(Reminder.due_date <= before_date)
        if status:
            stmt = stmt.where(Reminder.status == status)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_upcoming(self, before_date: date) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(Reminder).where(
            Reminder.due_date <= before_date,
            Reminder.status.in_([ReminderStatus.PENDING, ReminderStatus.SENT]),
        )
        result = await self.db.execute(stmt)
        return int(result.scalar_one())
