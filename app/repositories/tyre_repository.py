import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tyre import Tyre
from app.repositories.base import BaseRepository


class TyreRepository(BaseRepository[Tyre]):
    def __init__(self, db: AsyncSession):
        super().__init__(Tyre, db)

    async def list_by_vehicle(self, vehicle_id: uuid.UUID):
        result = await self.db.execute(select(Tyre).where(Tyre.vehicle_id == vehicle_id))
        return result.scalars().all()
