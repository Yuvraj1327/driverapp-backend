"""
Reminder endpoints: list, create, mark-read.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import pagination_params
from app.auth.dependencies import require_any_role, require_manager
from app.core.constants import ReminderStatus
from app.database.session import get_db
from app.schemas.common import Message, Page
from app.schemas.reminder import ReminderCreate, ReminderRead, ReminderUpdate
from app.services.reminder_service import ReminderService

router = APIRouter(prefix="/reminders", tags=["Reminders"])


@router.post(
    "", include_in_schema=False, response_model=ReminderRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_manager)],
)
@router.post(
    "/", response_model=ReminderRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_manager)],
)
async def create_reminder(payload: ReminderCreate, db: AsyncSession = Depends(get_db)) -> ReminderRead:
    service = ReminderService(db)
    reminder = await service.create(payload)
    return ReminderRead.model_validate(reminder)


@router.get("", include_in_schema=False, response_model=Page[ReminderRead], dependencies=[Depends(require_any_role)])
@router.get("/", response_model=Page[ReminderRead], dependencies=[Depends(require_any_role)])
async def list_reminders(
    pagination: tuple[int, int] = Depends(pagination_params),
    reminder_status: ReminderStatus | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> Page[ReminderRead]:
    page, page_size = pagination
    service = ReminderService(db)
    result = await service.list(page, page_size, reminder_status)
    return Page[ReminderRead](
        items=[ReminderRead.model_validate(r) for r in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )


@router.put("/{reminder_id}", response_model=ReminderRead, dependencies=[Depends(require_manager)])
async def update_reminder(
    reminder_id: uuid.UUID, payload: ReminderUpdate, db: AsyncSession = Depends(get_db)
) -> ReminderRead:
    service = ReminderService(db)
    reminder = await service.update(reminder_id, payload)
    return ReminderRead.model_validate(reminder)


@router.post(
    "/{reminder_id}/mark-read", response_model=ReminderRead, dependencies=[Depends(require_any_role)]
)
async def mark_reminder_read(reminder_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ReminderRead:
    service = ReminderService(db)
    reminder = await service.mark_read(reminder_id)
    return ReminderRead.model_validate(reminder)


@router.delete("/{reminder_id}", response_model=Message, dependencies=[Depends(require_manager)])
async def delete_reminder(reminder_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Message:
    service = ReminderService(db)
    await service.delete(reminder_id)
    return Message(detail="Reminder deleted successfully")
