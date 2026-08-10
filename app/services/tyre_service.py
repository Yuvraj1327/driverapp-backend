from __future__ import annotations
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tyre import Tyre
from app.repositories.tyre_repository import TyreRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.common import Page
from app.schemas.tyre import TyreCreate, TyreUpdate
from app.services.exceptions import NotFoundError


class TyreService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TyreRepository(db)
        self.vehicle_repo = VehicleRepository(db)

    async def create(self, data: TyreCreate) -> Tyre:
        if not await self.vehicle_repo.get(data.vehicle_id):
            raise NotFoundError("Vehicle", str(data.vehicle_id))
        return await self.repo.create(data.model_dump())

    async def get(self, tyre_id: uuid.UUID) -> Tyre:
        tyre = await self.repo.get(tyre_id)
        if not tyre:
            raise NotFoundError("Tyre", str(tyre_id))
        return tyre

    async def list(self, page: int, page_size: int, vehicle_id: uuid.UUID | None = None) -> Page[Tyre]:
        filters = {"vehicle_id": vehicle_id} if vehicle_id else None
        items, total = await self.repo.list(page=page, page_size=page_size, filters=filters)
        return Page.create(items=items, total=total, page=page, page_size=page_size)

    async def update(self, tyre_id: uuid.UUID, data: TyreUpdate) -> Tyre:
        tyre = await self.repo.get(tyre_id)
        if not tyre:
            raise NotFoundError("Tyre", str(tyre_id))
        return await self.repo.update(tyre, data.model_dump(exclude_unset=True))

    async def delete(self, tyre_id: uuid.UUID) -> None:
        tyre = await self.repo.get(tyre_id)
        if not tyre:
            raise NotFoundError("Tyre", str(tyre_id))
        await self.repo.delete(tyre)
