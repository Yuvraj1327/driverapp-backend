import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy import Date, Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ExpenseStatus
from app.database.base import Base, TimestampMixin, UUIDMixin


class Expense(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "expenses"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expense_categories.id", ondelete="RESTRICT"), nullable=False
    )

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    receipt_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[ExpenseStatus] = mapped_column(
        Enum(ExpenseStatus, name="expense_status"), default=ExpenseStatus.PENDING, nullable=False
    )

    vehicle: Mapped["Vehicle"] = relationship(back_populates="expenses")
    driver: Mapped["Driver"] = relationship(back_populates="expenses")
    category: Mapped["ExpenseCategory"] = relationship(back_populates="expenses")
    approvals: Mapped[List["ExpenseApproval"]] = relationship(
        back_populates="expense", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Expense {self.id} amount={self.amount} status={self.status}>"
