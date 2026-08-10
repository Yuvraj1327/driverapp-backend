from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense_approval import ExpenseApproval
from app.repositories.base import BaseRepository


class ExpenseApprovalRepository(BaseRepository[ExpenseApproval]):
    def __init__(self, db: AsyncSession):
        super().__init__(ExpenseApproval, db)
