from datetime import date
from typing import List, Optional

from sqlalchemy import Date, Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import VehicleStatus
from app.database.base import Base, TimestampMixin, UUIDMixin


class Vehicle(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "vehicles"

    registration_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    vin: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)

    current_odometer: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    mulkiya_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mulkiya_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    insurance_provider: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    insurance_policy_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    insurance_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    status: Mapped[VehicleStatus] = mapped_column(
        Enum(VehicleStatus, name="vehicle_status", values_callable=lambda x: [e.value for e in x]), default=VehicleStatus.ACTIVE, nullable=False
    )

    assignments: Mapped[List["VehicleAssignment"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )
    km_logs: Mapped[List["KmLog"]] = relationship(back_populates="vehicle", cascade="all, delete-orphan")
    expenses: Mapped[List["Expense"]] = relationship(back_populates="vehicle", cascade="all, delete-orphan")
    tyres: Mapped[List["Tyre"]] = relationship(back_populates="vehicle", cascade="all, delete-orphan")
    services: Mapped[List["Service"]] = relationship(back_populates="vehicle", cascade="all, delete-orphan")
    reminders: Mapped[List["Reminder"]] = relationship(back_populates="vehicle", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Vehicle {self.registration_number}>"
