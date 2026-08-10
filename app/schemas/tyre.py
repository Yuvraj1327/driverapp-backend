import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TyreBase(BaseModel):
    vehicle_id: uuid.UUID
    brand: str
    position: str
    serial_number: str | None = None
    installed_date: date = Field(default_factory=date.today)
    installed_odometer: float = Field(ge=0)
    expected_life_km: float = Field(default=50000.0, gt=0)
    cost: float | None = None
    condition: str | None = None
    notes: str | None = None


class TyreCreate(TyreBase):
    pass


class TyreUpdate(BaseModel):
    brand: str | None = None
    position: str | None = None
    serial_number: str | None = None
    removed_date: date | None = None
    condition: str | None = None
    notes: str | None = None
    cost: float | None = None


class TyreRead(TyreBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    removed_date: date | None = None
    created_at: datetime
    updated_at: datetime
