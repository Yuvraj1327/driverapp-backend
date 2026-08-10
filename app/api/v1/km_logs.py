"""
Daily KM entry endpoints with automatic distance calculation.
"""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import pagination_params
from app.auth.dependencies import require_any_role
from app.database.session import get_db
from app.schemas.common import Page
from app.schemas.km_log import KmLogCreate, KmLogRead, KmLogUpdate, KmStats
from app.services.km_log_service import KmLogService

router = APIRouter(prefix="/km-logs", tags=["KM Logs"])


@router.post(
    "", include_in_schema=False, response_model=KmLogRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_any_role)],
)
@router.post(
    "/", response_model=KmLogRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_any_role)],
)
async def create_km_log(payload: KmLogCreate, db: AsyncSession = Depends(get_db)) -> KmLogRead:
    service = KmLogService(db)
    log = await service.create_log(payload)
    return KmLogRead.model_validate(log)


@router.put("/{log_id}", response_model=KmLogRead, dependencies=[Depends(require_any_role)])
async def update_km_log(
    log_id: uuid.UUID, payload: KmLogUpdate, db: AsyncSession = Depends(get_db)
) -> KmLogRead:
    service = KmLogService(db)
    log = await service.update_log(log_id, payload)
    return KmLogRead.model_validate(log)


@router.get("/{log_id}", response_model=KmLogRead, dependencies=[Depends(require_any_role)])
async def get_km_log(log_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> KmLogRead:
    service = KmLogService(db)
    log = await service.get_log(log_id)
    return KmLogRead.model_validate(log)


@router.get(
    "/vehicle/{vehicle_id}/history", response_model=Page[KmLogRead], dependencies=[Depends(require_any_role)]
)
async def vehicle_km_history(
    vehicle_id: uuid.UUID,
    pagination: tuple[int, int] = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> Page[KmLogRead]:
    page, page_size = pagination
    service = KmLogService(db)
    result = await service.history_by_vehicle(vehicle_id, page, page_size)
    return Page[KmLogRead](
        items=[KmLogRead.model_validate(l) for l in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )


@router.get(
    "/driver/{driver_id}/history", response_model=Page[KmLogRead], dependencies=[Depends(require_any_role)]
)
async def driver_km_history(
    driver_id: uuid.UUID,
    pagination: tuple[int, int] = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
) -> Page[KmLogRead]:
    page, page_size = pagination
    service = KmLogService(db)
    result = await service.history_by_driver(driver_id, page, page_size)
    return Page[KmLogRead](
        items=[KmLogRead.model_validate(l) for l in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )


@router.get(
    "/vehicle/{vehicle_id}/stats", response_model=KmStats, dependencies=[Depends(require_any_role)],
    summary="Today / current-month / all-time KM totals for a vehicle",
)
async def vehicle_km_stats(vehicle_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> KmStats:
    service = KmLogService(db)
    return await service.stats_for_vehicle(vehicle_id)


@router.get(
    "/driver/{driver_id}/stats", response_model=KmStats, dependencies=[Depends(require_any_role)],
    summary="Today / current-month / all-time KM totals for a driver",
)
async def driver_km_stats(driver_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> KmStats:
    service = KmLogService(db)
    return await service.stats_for_driver(driver_id)
