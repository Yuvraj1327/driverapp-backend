import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class Service(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "services"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False
    )

    service_type: Mapped[str] = mapped_column(String(150), nullable=False)  # e.g. oil change
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    odometer_reading: Mapped[float] = mapped_column(Float, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    workshop_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    next_service_due_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    next_service_due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="services")

    def __repr__(self) -> str:
        return f"<Service {self.service_type} vehicle={self.vehicle_id}>"
