from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense_category import ExpenseCategory
from app.repositories.base import BaseRepository


class ExpenseCategoryRepository(BaseRepository[ExpenseCategory]):
    def __init__(self, db: AsyncSession):
        super().__init__(ExpenseCategory, db)

    async def get_by_name(self, name: str) -> ExpenseCategory | None:
        result = await self.db.execute(select(ExpenseCategory).where(ExpenseCategory.name == name))
        return result.scalar_one_or_none()
