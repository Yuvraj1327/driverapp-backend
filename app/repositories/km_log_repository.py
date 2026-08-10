import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.km_log import KmLog
from app.repositories.base import BaseRepository


class KmLogRepository(BaseRepository[KmLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(KmLog, db)

    async def list_by_vehicle(self, vehicle_id: uuid.UUID, page: int, page_size: int):
        stmt = select(KmLog).where(KmLog.vehicle_id == vehicle_id).order_by(KmLog.log_date.desc())
        count_stmt = select(func.count()).select_from(KmLog).where(KmLog.vehicle_id == vehicle_id)
        total = (await self.db.execute(count_stmt)).scalar_one()
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return result.scalars().all(), total

    async def list_by_driver(self, driver_id: uuid.UUID, page: int, page_size: int):
        stmt = select(KmLog).where(KmLog.driver_id == driver_id).order_by(KmLog.log_date.desc())
        count_stmt = select(func.count()).select_from(KmLog).where(KmLog.driver_id == driver_id)
        total = (await self.db.execute(count_stmt)).scalar_one()
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return result.scalars().all(), total

    async def total_distance_between(
        self, start: date, end: date, vehicle_id: uuid.UUID | None = None, driver_id: uuid.UUID | None = None
    ) -> float:
        stmt = select(func.coalesce(func.sum(KmLog.distance_covered), 0.0)).where(
            KmLog.log_date >= start, KmLog.log_date <= end
        )
        if vehicle_id:
            stmt = stmt.where(KmLog.vehicle_id == vehicle_id)
        if driver_id:
            stmt = stmt.where(KmLog.driver_id == driver_id)
        result = await self.db.execute(stmt)
        return float(result.scalar_one())
