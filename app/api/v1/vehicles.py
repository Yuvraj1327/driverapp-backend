"""
Vehicle CRUD endpoints.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import pagination_params
from app.auth.dependencies import require_admin, require_any_role, require_manager
from app.core.constants import VehicleStatus
from app.database.session import get_db
from app.schemas.common import Message, Page
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.post(
    "/", response_model=VehicleRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_manager)],
)
async def create_vehicle(payload: VehicleCreate, db: AsyncSession = Depends(get_db)) -> VehicleRead:
    service = VehicleService(db)
    vehicle = await service.create_vehicle(payload)
    return VehicleRead.model_validate(vehicle)


@router.get("/", response_model=Page[VehicleRead], dependencies=[Depends(require_any_role)])
async def list_vehicles(
    pagination: tuple[int, int] = Depends(pagination_params),
    status_filter: VehicleStatus | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> Page[VehicleRead]:
    page, page_size = pagination
    service = VehicleService(db)
    result = await service.list_vehicles(page, page_size, status=status_filter)
    return Page[VehicleRead](
        items=[VehicleRead.model_validate(v) for v in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )


@router.get("/{vehicle_id}", response_model=VehicleRead, dependencies=[Depends(require_any_role)])
async def get_vehicle(vehicle_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> VehicleRead:
    service = VehicleService(db)
    vehicle = await service.get_vehicle(vehicle_id)
    return VehicleRead.model_validate(vehicle)


@router.put("/{vehicle_id}", response_model=VehicleRead, dependencies=[Depends(require_manager)])
async def update_vehicle(
    vehicle_id: uuid.UUID, payload: VehicleUpdate, db: AsyncSession = Depends(get_db)
) -> VehicleRead:
    service = VehicleService(db)
    vehicle = await service.update_vehicle(vehicle_id, payload)
    return VehicleRead.model_validate(vehicle)


@router.delete("/{vehicle_id}", response_model=Message, dependencies=[Depends(require_admin)])
async def delete_vehicle(vehicle_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Message:
    service = VehicleService(db)
    await service.delete_vehicle(vehicle_id)
    return Message(detail="Vehicle deleted successfully")
