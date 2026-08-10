"""
Vehicle service (maintenance) history endpoints.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import pagination_params
from app.auth.dependencies import require_any_role, require_manager
from app.database.session import get_db
from app.schemas.common import Message, Page
from app.schemas.service import ServiceCreate, ServiceRead, ServiceUpdate
from app.services.service_history_service import ServiceHistoryService

router = APIRouter(prefix="/services", tags=["Service History"])


@router.post(
    "", include_in_schema=False, response_model=ServiceRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_manager)],
)
@router.post(
    "/", response_model=ServiceRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_manager)],
)
async def create_service(payload: ServiceCreate, db: AsyncSession = Depends(get_db)) -> ServiceRead:
    service = ServiceHistoryService(db)
    record = await service.create(payload)
    return ServiceRead.model_validate(record)


@router.get("", include_in_schema=False, response_model=Page[ServiceRead], dependencies=[Depends(require_any_role)])
@router.get("/", response_model=Page[ServiceRead], dependencies=[Depends(require_any_role)])
async def list_services(
    pagination: tuple[int, int] = Depends(pagination_params),
    vehicle_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Page[ServiceRead]:
    page, page_size = pagination
    service = ServiceHistoryService(db)
    result = await service.list(page, page_size, vehicle_id)
    return Page[ServiceRead](
        items=[ServiceRead.model_validate(s) for s in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )


@router.get("/{service_id}", response_model=ServiceRead, dependencies=[Depends(require_any_role)])
async def get_service(service_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ServiceRead:
    service = ServiceHistoryService(db)
    record = await service.get(service_id)
    return ServiceRead.model_validate(record)


@router.put("/{service_id}", response_model=ServiceRead, dependencies=[Depends(require_manager)])
async def update_service(
    service_id: uuid.UUID, payload: ServiceUpdate, db: AsyncSession = Depends(get_db)
) -> ServiceRead:
    service = ServiceHistoryService(db)
    record = await service.update(service_id, payload)
    return ServiceRead.model_validate(record)


@router.delete("/{service_id}", response_model=Message, dependencies=[Depends(require_manager)])
async def delete_service(service_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Message:
    service = ServiceHistoryService(db)
    await service.delete(service_id)
    return Message(detail="Service record deleted successfully")
