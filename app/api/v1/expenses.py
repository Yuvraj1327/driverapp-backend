"""
Expense CRUD, receipt upload, and approval workflow endpoints.
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import pagination_params
from app.auth.dependencies import get_current_user, require_any_role, require_manager
from app.core.constants import ExpenseStatus
from app.database.session import get_db
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.expense import ExpenseApprovalAction, ExpenseCreate, ExpenseRead, ExpenseUpdate
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post(
    "", include_in_schema=False, response_model=ExpenseRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_any_role)],
)
@router.post(
    "/", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_any_role)],
)
async def create_expense(payload: ExpenseCreate, db: AsyncSession = Depends(get_db)) -> ExpenseRead:
    service = ExpenseService(db)
    expense = await service.create_expense(payload)
    return ExpenseRead.model_validate(expense)


@router.get("", include_in_schema=False, response_model=Page[ExpenseRead], dependencies=[Depends(require_any_role)])
@router.get("/", response_model=Page[ExpenseRead], dependencies=[Depends(require_any_role)])
async def list_expenses(
    pagination: tuple[int, int] = Depends(pagination_params),
    vehicle_id: uuid.UUID | None = Query(default=None),
    driver_id: uuid.UUID | None = Query(default=None),
    category_id: uuid.UUID | None = Query(default=None),
    expense_status: ExpenseStatus | None = Query(default=None, alias="status"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Page[ExpenseRead]:
    page, page_size = pagination
    service = ExpenseService(db)
    result = await service.list_expenses(
        page, page_size, vehicle_id, driver_id, expense_status, category_id, start_date, end_date
    )
    return Page[ExpenseRead](
        items=[ExpenseRead.model_validate(e) for e in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )


@router.get("/{expense_id}", response_model=ExpenseRead, dependencies=[Depends(require_any_role)])
async def get_expense(expense_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ExpenseRead:
    service = ExpenseService(db)
    expense = await service.get_expense(expense_id)
    return ExpenseRead.model_validate(expense)


@router.put("/{expense_id}", response_model=ExpenseRead, dependencies=[Depends(require_any_role)])
async def update_expense(
    expense_id: uuid.UUID, payload: ExpenseUpdate, db: AsyncSession = Depends(get_db)
) -> ExpenseRead:
    service = ExpenseService(db)
    expense = await service.update_expense(expense_id, payload)
    return ExpenseRead.model_validate(expense)


@router.delete("/{expense_id}", response_model=Message, dependencies=[Depends(require_manager)])
async def delete_expense(expense_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Message:
    service = ExpenseService(db)
    await service.delete_expense(expense_id)
    return Message(detail="Expense deleted successfully")


@router.post(
    "/{expense_id}/receipt", response_model=ExpenseRead, dependencies=[Depends(require_any_role)]
)
async def upload_receipt(
    expense_id: uuid.UUID, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
) -> ExpenseRead:
    service = ExpenseService(db)
    expense = await service.upload_receipt(expense_id, file)
    return ExpenseRead.model_validate(expense)


@router.post(
    "/{expense_id}/review", response_model=ExpenseRead, dependencies=[Depends(require_manager)]
)
async def review_expense(
    expense_id: uuid.UUID,
    payload: ExpenseApprovalAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExpenseRead:
    service = ExpenseService(db)
    expense = await service.review_expense(expense_id, current_user, payload.decision, payload.remarks)
    return ExpenseRead.model_validate(expense)
