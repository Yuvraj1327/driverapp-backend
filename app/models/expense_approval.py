import uuid
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ExpenseStatus
from app.database.base import Base, TimestampMixin, UUIDMixin


class ExpenseApproval(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "expense_approvals"

    expense_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    decision: Mapped[ExpenseStatus] = mapped_column(
        Enum(ExpenseStatus, name="approval_decision", values_callable=lambda x: [e.value for e in x]), nullable=False
    )
    remarks: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    expense: Mapped["Expense"] = relationship(back_populates="approvals")
    reviewer: Mapped[Optional["User"]] = relationship()

    def __repr__(self) -> str:
        return f"<ExpenseApproval expense={self.expense_id} decision={self.decision}>"
