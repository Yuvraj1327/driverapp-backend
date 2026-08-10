from typing import List, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class ExpenseCategory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "expense_categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    expenses: Mapped[List["Expense"]] = relationship(back_populates="category")

    def __repr__(self) -> str:
        return f"<ExpenseCategory {self.name}>"
