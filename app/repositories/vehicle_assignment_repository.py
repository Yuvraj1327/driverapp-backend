import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AssignmentStatus
from app.models.vehicle_assignment import VehicleAssignment
from app.repositories.base import BaseRepository


class VehicleAssignmentRepository(BaseRepository[VehicleAssignment]):
    def __init__(self, db: AsyncSession):
        super().__init__(VehicleAssignment, db)

    async def get_active_for_vehicle(self, vehicle_id: uuid.UUID) -> VehicleAssignment | None:
        result = await self.db.execute(
            select(VehicleAssignment).where(
                VehicleAssignment.vehicle_id == vehicle_id,
                VehicleAssignment.status == AssignmentStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_for_driver(self, driver_id: uuid.UUID) -> VehicleAssignment | None:
        result = await self.db.execute(
            select(VehicleAssignment).where(
                VehicleAssignment.driver_id == driver_id,
                VehicleAssignment.status == AssignmentStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()
