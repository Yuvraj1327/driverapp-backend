import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class Driver(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "drivers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    user: Mapped["User"] = relationship(back_populates="driver_profile")

    license_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    license_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    is_available: Mapped[bool] = mapped_column(default=True, nullable=False)

    assignments: Mapped[List["VehicleAssignment"]] = relationship(
        back_populates="driver", cascade="all, delete-orphan"
    )
    km_logs: Mapped[List["KmLog"]] = relationship(back_populates="driver", cascade="all, delete-orphan")
    expenses: Mapped[List["Expense"]] = relationship(back_populates="driver", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Driver {self.license_number}>"
