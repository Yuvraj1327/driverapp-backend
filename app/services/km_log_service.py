"""
KM log service: auto-calculates distance and updates vehicle odometer.
"""
from __future__ import annotations
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.km_log import KmLog
from app.repositories.km_log_repository import KmLogRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.common import Page
from app.schemas.km_log import KmLogCreate, KmLogUpdate
from app.services.exceptions import NotFoundError, ValidationError


class KmLogService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.km_log_repo = KmLogRepository(db)
        self.vehicle_repo = VehicleRepository(db)

    async def create_log(self, data: KmLogCreate) -> KmLog:
        vehicle = await self.vehicle_repo.get(data.vehicle_id)
        if not vehicle:
            raise NotFoundError("Vehicle", str(data.vehicle_id))

        if data.start_odometer < vehicle.current_odometer - 0.01:
            raise ValidationError(
                f"start_odometer ({data.start_odometer}) cannot be less than the vehicle's "
                f"current recorded odometer ({vehicle.current_odometer})"
            )

        distance = round(data.end_odometer - data.start_odometer, 2)
        log = await self.km_log_repo.create(
            {
                "vehicle_id": data.vehicle_id,
                "driver_id": data.driver_id,
                "log_date": data.log_date,
                "start_odometer": data.start_odometer,
                "end_odometer": data.end_odometer,
                "distance_covered": distance,
                "trip_purpose": data.trip_purpose,
                "notes": data.notes,
            }
        )
        vehicle.current_odometer = data.end_odometer
        await self.db.commit()
        return log

    async def update_log(self, log_id: uuid.UUID, data: KmLogUpdate) -> KmLog:
        log = await self.km_log_repo.get(log_id)
        if not log:
            raise NotFoundError("KmLog", str(log_id))

        update_data = data.model_dump(exclude_unset=True)
        new_end = update_data.get("end_odometer", log.end_odometer)
        if new_end < log.start_odometer:
            raise ValidationError("end_odometer cannot be less than start_odometer")
        update_data["distance_covered"] = round(new_end - log.start_odometer, 2)

        log = await self.km_log_repo.update(log, update_data)

        vehicle = await self.vehicle_repo.get(log.vehicle_id)
        if vehicle and vehicle.current_odometer < log.end_odometer:
            vehicle.current_odometer = log.end_odometer
            await self.db.commit()
        return log

    async def get_log(self, log_id: uuid.UUID) -> KmLog:
        log = await self.km_log_repo.get(log_id)
        if not log:
            raise NotFoundError("KmLog", str(log_id))
        return log

    async def history_by_vehicle(self, vehicle_id: uuid.UUID, page: int, page_size: int) -> Page[KmLog]:
        items, total = await self.km_log_repo.list_by_vehicle(vehicle_id, page, page_size)
        return Page.create(items=items, total=total, page=page, page_size=page_size)

    async def history_by_driver(self, driver_id: uuid.UUID, page: int, page_size: int) -> Page[KmLog]:
        items, total = await self.km_log_repo.list_by_driver(driver_id, page, page_size)
        return Page.create(items=items, total=total, page=page, page_size=page_size)
