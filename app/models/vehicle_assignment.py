import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import AssignmentStatus
from app.database.base import Base, TimestampMixin, UUIDMixin


class VehicleAssignment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "vehicle_assignments"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False
    )

    assigned_date: Mapped[date] = mapped_column(Date, nullable=False)
    unassigned_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[AssignmentStatus] = mapped_column(
        Enum(AssignmentStatus, name="assignment_status"), default=AssignmentStatus.ACTIVE, nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="assignments")
    driver: Mapped["Driver"] = relationship(back_populates="assignments")

    def __repr__(self) -> str:
        return f"<VehicleAssignment vehicle={self.vehicle_id} driver={self.driver_id}>"
