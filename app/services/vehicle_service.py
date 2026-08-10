from __future__ import annotations
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.common import Page
from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.services.exceptions import ConflictError, NotFoundError


class VehicleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vehicle_repo = VehicleRepository(db)

    async def create_vehicle(self, data: VehicleCreate) -> Vehicle:
        existing = await self.vehicle_repo.get_by_registration(data.registration_number)
        if existing:
            raise ConflictError(
                f"A vehicle with registration '{data.registration_number}' already exists"
            )
        return await self.vehicle_repo.create(data.model_dump())

    async def get_vehicle(self, vehicle_id: uuid.UUID) -> Vehicle:
        vehicle = await self.vehicle_repo.get(vehicle_id)
        if not vehicle:
            raise NotFoundError("Vehicle", str(vehicle_id))
        return vehicle

    async def list_vehicles(self, page: int, page_size: int, status=None) -> Page[Vehicle]:
        filters = {"status": status} if status else None
        items, total = await self.vehicle_repo.list(page=page, page_size=page_size, filters=filters)
        return Page.create(items=items, total=total, page=page, page_size=page_size)

    async def update_vehicle(self, vehicle_id: uuid.UUID, data: VehicleUpdate) -> Vehicle:
        vehicle = await self.vehicle_repo.get(vehicle_id)
        if not vehicle:
            raise NotFoundError("Vehicle", str(vehicle_id))
        return await self.vehicle_repo.update(vehicle, data.model_dump(exclude_unset=True))

    async def delete_vehicle(self, vehicle_id: uuid.UUID) -> None:
        vehicle = await self.vehicle_repo.get(vehicle_id)
        if not vehicle:
            raise NotFoundError("Vehicle", str(vehicle_id))
        await self.vehicle_repo.delete(vehicle)
