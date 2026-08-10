import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class KmLogCreate(BaseModel):
    vehicle_id: uuid.UUID
    driver_id: uuid.UUID
    log_date: date = Field(default_factory=date.today)
    start_odometer: float = Field(ge=0)
    end_odometer: float = Field(ge=0)
    trip_purpose: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_odometer(self) -> "KmLogCreate":
        if self.end_odometer < self.start_odometer:
            raise ValueError("end_odometer must be greater than or equal to start_odometer")
        return self


class KmLogUpdate(BaseModel):
    end_odometer: float | None = Field(default=None, ge=0)
    trip_purpose: str | None = None
    notes: str | None = None


class KmLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vehicle_id: uuid.UUID
    driver_id: uuid.UUID
    log_date: date
    start_odometer: float
    end_odometer: float
    distance_covered: float
    trip_purpose: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class KmStats(BaseModel):
    """Aggregate KM stats — used by the Flutter dashboard/vehicle-detail screens
    to show today/this-month/all-time distance covered without needing to
    walk the full history."""

    today_km: float
    current_month_km: float
    total_km: float
