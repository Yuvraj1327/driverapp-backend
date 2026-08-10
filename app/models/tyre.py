import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class Tyre(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tyres"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False
    )

    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. front-left
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    installed_date: Mapped[date] = mapped_column(Date, nullable=False)
    installed_odometer: Mapped[float] = mapped_column(Float, nullable=False)
    expected_life_km: Mapped[float] = mapped_column(Float, default=50000.0, nullable=False)
    removed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    condition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="tyres")

    def __repr__(self) -> str:
        return f"<Tyre {self.brand} {self.position} vehicle={self.vehicle_id}>"
