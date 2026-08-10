"""
Expense category CRUD endpoints.
"""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import pagination_params
from app.auth.dependencies import require_any_role, require_manager
from app.database.session import get_db
from app.schemas.common import Message, Page
from app.schemas.expense_category import (
    ExpenseCategoryCreate,
    ExpenseCategoryRead,
    ExpenseCategoryUpdate,
)
from app.services.expense_category_service import ExpenseCategoryService

router = APIRouter(prefix="/expense-categories", tags=["Expense Categories"])


@router.post(
    "/", response_model=ExpenseCategoryRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_manager)],
)
async def create_category(
    payload: ExpenseCategoryCreate, db: AsyncSession = Depends(get_db)
) -> ExpenseCategoryRead:
    service = ExpenseCategoryService(db)
    category = await service.create(payload)
    return ExpenseCategoryRead.model_validate(category)


@router.get("/", response_model=Page[ExpenseCategoryRead], dependencies=[Depends(require_any_role)])
async def list_categories(
    pagination: tuple[int, int] = Depends(pagination_params), db: AsyncSession = Depends(get_db)
) -> Page[ExpenseCategoryRead]:
    page, page_size = pagination
    service = ExpenseCategoryService(db)
    result = await service.list(page, page_size)
    return Page[ExpenseCategoryRead](
        items=[ExpenseCategoryRead.model_validate(c) for c in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )


@router.put(
    "/{category_id}", response_model=ExpenseCategoryRead, dependencies=[Depends(require_manager)]
)
async def update_category(
    category_id: uuid.UUID, payload: ExpenseCategoryUpdate, db: AsyncSession = Depends(get_db)
) -> ExpenseCategoryRead:
    service = ExpenseCategoryService(db)
    category = await service.update(category_id, payload)
    return ExpenseCategoryRead.model_validate(category)


@router.delete("/{category_id}", response_model=Message, dependencies=[Depends(require_manager)])
async def delete_category(category_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Message:
    service = ExpenseCategoryService(db)
    await service.delete(category_id)
    return Message(detail="Expense category deleted successfully")
