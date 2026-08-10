import uuid
from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ExpenseStatus
from app.models.expense import Expense
from app.repositories.base import BaseRepository


class ExpenseRepository(BaseRepository[Expense]):
    def __init__(self, db: AsyncSession):
        super().__init__(Expense, db)

    async def list_filtered(
        self,
        page: int,
        page_size: int,
        vehicle_id: uuid.UUID | None = None,
        driver_id: uuid.UUID | None = None,
        status: ExpenseStatus | None = None,
        category_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ):
        stmt = select(Expense)
        count_stmt = select(func.count()).select_from(Expense)

        conditions: list[Any] = []
        if vehicle_id:
            conditions.append(Expense.vehicle_id == vehicle_id)
        if driver_id:
            conditions.append(Expense.driver_id == driver_id)
        if status:
            conditions.append(Expense.status == status)
        if category_id:
            conditions.append(Expense.category_id == category_id)
        if start_date:
            conditions.append(Expense.expense_date >= start_date)
        if end_date:
            conditions.append(Expense.expense_date <= end_date)

        for c in conditions:
            stmt = stmt.where(c)
            count_stmt = count_stmt.where(c)

        stmt = stmt.order_by(Expense.expense_date.desc())
        total = (await self.db.execute(count_stmt)).scalar_one()
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return result.scalars().all(), total

    async def total_amount_between(
        self, start: date, end: date, vehicle_id: uuid.UUID | None = None, driver_id: uuid.UUID | None = None,
        status: ExpenseStatus | None = None,
    ) -> float:
        stmt = select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
            Expense.expense_date >= start, Expense.expense_date <= end
        )
        if vehicle_id:
            stmt = stmt.where(Expense.vehicle_id == vehicle_id)
        if driver_id:
            stmt = stmt.where(Expense.driver_id == driver_id)
        if status:
            stmt = stmt.where(Expense.status == status)
        result = await self.db.execute(stmt)
        return float(result.scalar_one())

    async def count_pending(self) -> int:
        stmt = select(func.count()).select_from(Expense).where(Expense.status == ExpenseStatus.PENDING)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def expense_by_category_between(self, start: date, end: date):
        from app.models.expense_category import ExpenseCategory

        stmt = (
            select(
                ExpenseCategory.name,
                func.coalesce(func.sum(Expense.amount), 0.0),
                func.count(Expense.id),
            )
            .join(Expense, Expense.category_id == ExpenseCategory.id)
            .where(Expense.expense_date >= start, Expense.expense_date <= end)
            .group_by(ExpenseCategory.name)
        )
        result = await self.db.execute(stmt)
        return result.all()
