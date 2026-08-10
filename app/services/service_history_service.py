"""
Vehicle service (maintenance) history. Named 'service_history_service' to avoid
clashing with the generic term 'service layer'.
"""
from __future__ import annotations
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service
from app.repositories.service_repository import ServiceRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.common import Page
from app.schemas.service import ServiceCreate, ServiceUpdate
from app.services.exceptions import NotFoundError


class ServiceHistoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ServiceRepository(db)
        self.vehicle_repo = VehicleRepository(db)

    async def create(self, data: ServiceCreate) -> Service:
        vehicle = await self.vehicle_repo.get(data.vehicle_id)
        if not vehicle:
            raise NotFoundError("Vehicle", str(data.vehicle_id))
        service = await self.repo.create(data.model_dump())
        if vehicle.current_odometer < data.odometer_reading:
            vehicle.current_odometer = data.odometer_reading
            await self.db.commit()
        return service

    async def get(self, service_id: uuid.UUID) -> Service:
        service = await self.repo.get(service_id)
        if not service:
            raise NotFoundError("Service", str(service_id))
        return service

    async def list(self, page: int, page_size: int, vehicle_id: uuid.UUID | None = None) -> Page[Service]:
        filters = {"vehicle_id": vehicle_id} if vehicle_id else None
        items, total = await self.repo.list(page=page, page_size=page_size, filters=filters)
        return Page.create(items=items, total=total, page=page, page_size=page_size)

    async def update(self, service_id: uuid.UUID, data: ServiceUpdate) -> Service:
        service = await self.repo.get(service_id)
        if not service:
            raise NotFoundError("Service", str(service_id))
        return await self.repo.update(service, data.model_dump(exclude_unset=True))

    async def delete(self, service_id: uuid.UUID) -> None:
        service = await self.repo.get(service_id)
        if not service:
            raise NotFoundError("Service", str(service_id))
        await self.repo.delete(service)
