"""
Expense CRUD, receipt upload, and approval workflow.
"""
from __future__ import annotations
import uuid
from datetime import date

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ExpenseStatus, NotificationType, RoleName
from app.models.expense import Expense
from app.models.user import User
from app.repositories.driver_repository import DriverRepository
from app.repositories.expense_approval_repository import ExpenseApprovalRepository
from app.repositories.expense_category_repository import ExpenseCategoryRepository
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.common import Page
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.exceptions import ConflictError, NotFoundError, ValidationError
from app.utils.storage import StorageError, upload_receipt


class ExpenseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.expense_repo = ExpenseRepository(db)
        self.vehicle_repo = VehicleRepository(db)
        self.driver_repo = DriverRepository(db)
        self.category_repo = ExpenseCategoryRepository(db)
        self.approval_repo = ExpenseApprovalRepository(db)
        self.user_repo = UserRepository(db)
        self.notification_repo = NotificationRepository(db)

    async def create_expense(self, data: ExpenseCreate) -> Expense:
        if not await self.vehicle_repo.get(data.vehicle_id):
            raise NotFoundError("Vehicle", str(data.vehicle_id))
        if not await self.driver_repo.get(data.driver_id):
            raise NotFoundError("Driver", str(data.driver_id))
        if not await self.category_repo.get(data.category_id):
            raise NotFoundError("ExpenseCategory", str(data.category_id))

        expense = await self.expense_repo.create(data.model_dump())

        # Notify all managers/admins about a new pending expense
        managers = await self._get_users_by_roles([RoleName.ADMIN, RoleName.MANAGER])
        for manager in managers:
            await self.notification_repo.create(
                {
                    "user_id": manager.id,
                    "title": "New expense pending approval",
                    "message": f"A new expense of {data.amount} was submitted and needs review.",
                    "notification_type": NotificationType.APPROVAL,
                    "link": f"/expenses/{expense.id}",
                }
            )
        return expense

    async def _get_users_by_roles(self, roles: list[RoleName]) -> list[User]:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from app.models.role import Role

        result = await self.db.execute(
            select(User)
            .join(Role, User.role_id == Role.id)
            .options(selectinload(User.role))
            .where(Role.name.in_([r.value for r in roles]))
        )
        return list(result.scalars().all())

    async def get_expense(self, expense_id: uuid.UUID) -> Expense:
        expense = await self.expense_repo.get(expense_id)
        if not expense:
            raise NotFoundError("Expense", str(expense_id))
        return expense

    async def list_expenses(
        self,
        page: int,
        page_size: int,
        vehicle_id: uuid.UUID | None = None,
        driver_id: uuid.UUID | None = None,
        status: ExpenseStatus | None = None,
        category_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Page[Expense]:
        items, total = await self.expense_repo.list_filtered(
            page, page_size, vehicle_id, driver_id, status, category_id, start_date, end_date
        )
        return Page.create(items=items, total=total, page=page, page_size=page_size)

    async def update_expense(self, expense_id: uuid.UUID, data: ExpenseUpdate) -> Expense:
        expense = await self.expense_repo.get(expense_id)
        if not expense:
            raise NotFoundError("Expense", str(expense_id))
        if expense.status != ExpenseStatus.PENDING:
            raise ConflictError("Only pending expenses can be edited")
        return await self.expense_repo.update(expense, data.model_dump(exclude_unset=True))

    async def delete_expense(self, expense_id: uuid.UUID) -> None:
        expense = await self.expense_repo.get(expense_id)
        if not expense:
            raise NotFoundError("Expense", str(expense_id))
        await self.expense_repo.delete(expense)

    async def upload_receipt(self, expense_id: uuid.UUID, file: UploadFile) -> Expense:
        expense = await self.expense_repo.get(expense_id)
        if not expense:
            raise NotFoundError("Expense", str(expense_id))
        try:
            url = await upload_receipt(file, subfolder=f"expenses/{expense_id}")
        except StorageError as exc:
            raise ValidationError(str(exc)) from exc
        return await self.expense_repo.update(expense, {"receipt_url": url})

    async def review_expense(
        self, expense_id: uuid.UUID, reviewer: User, decision: ExpenseStatus, remarks: str | None
    ) -> Expense:
        expense = await self.expense_repo.get(expense_id)
        if not expense:
            raise NotFoundError("Expense", str(expense_id))
        if expense.status != ExpenseStatus.PENDING:
            raise ConflictError("This expense has already been reviewed")
        if decision == ExpenseStatus.PENDING:
            raise ValidationError("Decision must be 'approved' or 'rejected'")

        expense = await self.expense_repo.update(expense, {"status": decision})
        await self.approval_repo.create(
            {
                "expense_id": expense.id,
                "reviewer_id": reviewer.id,
                "decision": decision,
                "remarks": remarks,
            }
        )

        # Notify the driver who submitted the expense
        driver = await self.driver_repo.get(expense.driver_id)
        if driver:
            await self.notification_repo.create(
                {
                    "user_id": driver.user_id,
                    "title": f"Expense {decision.value}",
                    "message": f"Your expense of {expense.amount} was {decision.value}.",
                    "notification_type": NotificationType.APPROVAL,
                    "link": f"/expenses/{expense.id}",
                }
            )
        return expense
