import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service
from app.repositories.base import BaseRepository


class ServiceRepository(BaseRepository[Service]):
    def __init__(self, db: AsyncSession):
        super().__init__(Service, db)

    async def list_by_vehicle(self, vehicle_id: uuid.UUID):
        result = await self.db.execute(
            select(Service).where(Service.vehicle_id == vehicle_id).order_by(Service.service_date.desc())
        )
        return result.scalars().all()

    async def count_between(self, start: date, end: date, vehicle_id: uuid.UUID | None = None) -> int:
        stmt = select(func.count()).select_from(Service).where(
            Service.service_date >= start, Service.service_date <= end
        )
        if vehicle_id:
            stmt = stmt.where(Service.vehicle_id == vehicle_id)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def total_cost_between(self, start: date, end: date, vehicle_id: uuid.UUID | None = None) -> float:
        stmt = select(func.coalesce(func.sum(Service.cost), 0.0)).where(
            Service.service_date >= start, Service.service_date <= end
        )
        if vehicle_id:
            stmt = stmt.where(Service.vehicle_id == vehicle_id)
        result = await self.db.execute(stmt)
        return float(result.scalar_one())
