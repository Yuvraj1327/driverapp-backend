import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.driver import Driver
from app.repositories.base import BaseRepository


class DriverRepository(BaseRepository[Driver]):
    def __init__(self, db: AsyncSession):
        super().__init__(Driver, db)

    async def get_with_user(self, id: uuid.UUID) -> Driver | None:
        result = await self.db.execute(
            select(Driver).options(selectinload(Driver.user)).where(Driver.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> Driver | None:
        result = await self.db.execute(select(Driver).where(Driver.user_id == user_id))
        return result.scalar_one_or_none()

    async def list_with_user(self, page: int, page_size: int):
        from sqlalchemy import func

        stmt = select(Driver).options(selectinload(Driver.user))
        count_stmt = select(func.count()).select_from(Driver)
        total = (await self.db.execute(count_stmt)).scalar_one()
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return result.scalars().all(), total
