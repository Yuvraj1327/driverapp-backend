from __future__ import annotations
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense_category import ExpenseCategory
from app.repositories.expense_category_repository import ExpenseCategoryRepository
from app.schemas.common import Page
from app.schemas.expense_category import ExpenseCategoryCreate, ExpenseCategoryUpdate
from app.services.exceptions import ConflictError, NotFoundError


class ExpenseCategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ExpenseCategoryRepository(db)

    async def create(self, data: ExpenseCategoryCreate) -> ExpenseCategory:
        if await self.repo.get_by_name(data.name):
            raise ConflictError(f"Category '{data.name}' already exists")
        return await self.repo.create(data.model_dump())

    async def get(self, category_id: uuid.UUID) -> ExpenseCategory:
        category = await self.repo.get(category_id)
        if not category:
            raise NotFoundError("ExpenseCategory", str(category_id))
        return category

    async def list(self, page: int, page_size: int) -> Page[ExpenseCategory]:
        items, total = await self.repo.list(page=page, page_size=page_size)
        return Page.create(items=items, total=total, page=page, page_size=page_size)

    async def update(self, category_id: uuid.UUID, data: ExpenseCategoryUpdate) -> ExpenseCategory:
        category = await self.repo.get(category_id)
        if not category:
            raise NotFoundError("ExpenseCategory", str(category_id))
        return await self.repo.update(category, data.model_dump(exclude_unset=True))

    async def delete(self, category_id: uuid.UUID) -> None:
        category = await self.repo.get(category_id)
        if not category:
            raise NotFoundError("ExpenseCategory", str(category_id))
        await self.repo.delete(category)
