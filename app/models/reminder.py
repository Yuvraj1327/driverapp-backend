import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ReminderStatus, ReminderType
from app.database.base import Base, TimestampMixin, UUIDMixin


class Reminder(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "reminders"

    vehicle_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=True
    )
    driver_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=True
    )

    reminder_type: Mapped[ReminderType] = mapped_column(
        Enum(ReminderType, name="reminder_type"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ReminderStatus] = mapped_column(
        Enum(ReminderStatus, name="reminder_status"), default=ReminderStatus.PENDING, nullable=False
    )

    vehicle: Mapped[Optional["Vehicle"]] = relationship(back_populates="reminders")
    driver: Mapped[Optional["Driver"]] = relationship()

    def __repr__(self) -> str:
        return f"<Reminder {self.title} due={self.due_date}>"
