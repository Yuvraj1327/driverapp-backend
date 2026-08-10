"""
Driver CRUD endpoints.
"""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import pagination_params
from app.auth.dependencies import require_admin, require_any_role, require_manager
from app.database.session import get_db
from app.schemas.common import Message, Page
from app.schemas.driver import DriverCreate, DriverUpdate, DriverWithUser
from app.services.driver_service import DriverService

router = APIRouter(prefix="/drivers", tags=["Drivers"])


def _to_schema(driver) -> DriverWithUser:
    return DriverWithUser(
        id=driver.id,
        user_id=driver.user_id,
        license_number=driver.license_number,
        license_expiry=driver.license_expiry,
        address=driver.address,
        emergency_contact=driver.emergency_contact,
        is_available=driver.is_available,
        created_at=driver.created_at,
        updated_at=driver.updated_at,
        full_name=driver.user.full_name if driver.user else None,
        email=driver.user.email if driver.user else None,
        phone=driver.user.phone if driver.user else None,
    )


@router.post(
    "", include_in_schema=False, response_model=DriverWithUser, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_manager)],
)
@router.post(
    "/", response_model=DriverWithUser, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_manager)],
)
async def create_driver(payload: DriverCreate, db: AsyncSession = Depends(get_db)) -> DriverWithUser:
    service = DriverService(db)
    driver = await service.create_driver(payload)
    return _to_schema(driver)


@router.get("", include_in_schema=False, response_model=Page[DriverWithUser], dependencies=[Depends(require_any_role)])
@router.get("/", response_model=Page[DriverWithUser], dependencies=[Depends(require_any_role)])
async def list_drivers(
    pagination: tuple[int, int] = Depends(pagination_params), db: AsyncSession = Depends(get_db)
) -> Page[DriverWithUser]:
    page, page_size = pagination
    service = DriverService(db)
    result = await service.list_drivers(page, page_size)
    return Page[DriverWithUser](
        items=[_to_schema(d) for d in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )


@router.get("/{driver_id}", response_model=DriverWithUser, dependencies=[Depends(require_any_role)])
async def get_driver(driver_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> DriverWithUser:
    service = DriverService(db)
    driver = await service.get_driver(driver_id)
    return _to_schema(driver)


@router.put("/{driver_id}", response_model=DriverWithUser, dependencies=[Depends(require_manager)])
async def update_driver(
    driver_id: uuid.UUID, payload: DriverUpdate, db: AsyncSession = Depends(get_db)
) -> DriverWithUser:
    service = DriverService(db)
    driver = await service.update_driver(driver_id, payload)
    return _to_schema(driver)


@router.delete("/{driver_id}", response_model=Message, dependencies=[Depends(require_admin)])
async def delete_driver(driver_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Message:
    service = DriverService(db)
    await service.delete_driver(driver_id)
    return Message(detail="Driver deleted successfully")
