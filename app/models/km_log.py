import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class KmLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "km_logs"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False
    )

    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_odometer: Mapped[float] = mapped_column(Float, nullable=False)
    end_odometer: Mapped[float] = mapped_column(Float, nullable=False)
    distance_covered: Mapped[float] = mapped_column(Float, nullable=False)
    trip_purpose: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="km_logs")
    driver: Mapped["Driver"] = relationship(back_populates="km_logs")

    def __repr__(self) -> str:
        return f"<KmLog vehicle={self.vehicle_id} date={self.log_date} dist={self.distance_covered}>"
