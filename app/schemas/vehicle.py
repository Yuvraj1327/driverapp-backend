import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import VehicleStatus


class VehicleBase(BaseModel):
    registration_number: str = Field(min_length=2, max_length=50)
    make: str
    model: str
    year: int = Field(ge=1980, le=2100)
    color: str | None = None
    vin: str | None = None
    mulkiya_number: str | None = None
    mulkiya_expiry: date | None = None
    insurance_provider: str | None = None
    insurance_policy_number: str | None = None
    insurance_expiry: date | None = None


class VehicleCreate(VehicleBase):
    current_odometer: float = Field(default=0.0, ge=0)


class VehicleUpdate(BaseModel):
    make: str | None = None
    model: str | None = None
    year: int | None = None
    color: str | None = None
    vin: str | None = None
    mulkiya_number: str | None = None
    mulkiya_expiry: date | None = None
    insurance_provider: str | None = None
    insurance_policy_number: str | None = None
    insurance_expiry: date | None = None
    status: VehicleStatus | None = None
    current_odometer: float | None = Field(default=None, ge=0)


class VehicleRead(VehicleBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    current_odometer: float
    status: VehicleStatus
    created_at: datetime
    updated_at: datetime
