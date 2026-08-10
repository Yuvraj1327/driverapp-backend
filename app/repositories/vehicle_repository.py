from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle
from app.repositories.base import BaseRepository


class VehicleRepository(BaseRepository[Vehicle]):
    def __init__(self, db: AsyncSession):
        super().__init__(Vehicle, db)

    async def get_by_registration(self, registration_number: str) -> Vehicle | None:
        result = await self.db.execute(
            select(Vehicle).where(Vehicle.registration_number == registration_number)
        )
        return result.scalar_one_or_none()

    async def list_expiring_documents(self, before_date: date) -> list[Vehicle]:
        stmt = select(Vehicle).where(
            (Vehicle.insurance_expiry <= before_date) | (Vehicle.mulkiya_expiry <= before_date)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
