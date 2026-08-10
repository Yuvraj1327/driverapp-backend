"""
Tyre management CRUD endpoints.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import pagination_params
from app.auth.dependencies import require_any_role, require_manager
from app.database.session import get_db
from app.schemas.common import Message, Page
from app.schemas.tyre import TyreCreate, TyreRead, TyreUpdate
from app.services.tyre_service import TyreService

router = APIRouter(prefix="/tyres", tags=["Tyres"])


@router.post(
    "", include_in_schema=False, response_model=TyreRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager)]
)
@router.post(
    "/", response_model=TyreRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager)]
)
async def create_tyre(payload: TyreCreate, db: AsyncSession = Depends(get_db)) -> TyreRead:
    service = TyreService(db)
    tyre = await service.create(payload)
    return TyreRead.model_validate(tyre)


@router.get("", include_in_schema=False, response_model=Page[TyreRead], dependencies=[Depends(require_any_role)])
@router.get("/", response_model=Page[TyreRead], dependencies=[Depends(require_any_role)])
async def list_tyres(
    pagination: tuple[int, int] = Depends(pagination_params),
    vehicle_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Page[TyreRead]:
    page, page_size = pagination
    service = TyreService(db)
    result = await service.list(page, page_size, vehicle_id)
    return Page[TyreRead](
        items=[TyreRead.model_validate(t) for t in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )


@router.get("/{tyre_id}", response_model=TyreRead, dependencies=[Depends(require_any_role)])
async def get_tyre(tyre_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> TyreRead:
    service = TyreService(db)
    tyre = await service.get(tyre_id)
    return TyreRead.model_validate(tyre)


@router.put("/{tyre_id}", response_model=TyreRead, dependencies=[Depends(require_manager)])
async def update_tyre(tyre_id: uuid.UUID, payload: TyreUpdate, db: AsyncSession = Depends(get_db)) -> TyreRead:
    service = TyreService(db)
    tyre = await service.update(tyre_id, payload)
    return TyreRead.model_validate(tyre)


@router.delete("/{tyre_id}", response_model=Message, dependencies=[Depends(require_manager)])
async def delete_tyre(tyre_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Message:
    service = TyreService(db)
    await service.delete(tyre_id)
    return Message(detail="Tyre record deleted successfully")
