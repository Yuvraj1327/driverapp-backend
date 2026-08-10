import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ServiceBase(BaseModel):
    vehicle_id: uuid.UUID
    service_type: str
    service_date: date = Field(default_factory=date.today)
    odometer_reading: float = Field(ge=0)
    cost: float = Field(ge=0)
    workshop_name: str | None = None
    next_service_due_km: float | None = None
    next_service_due_date: date | None = None
    notes: str | None = None


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    service_type: str | None = None
    service_date: date | None = None
    odometer_reading: float | None = None
    cost: float | None = None
    workshop_name: str | None = None
    next_service_due_km: float | None = None
    next_service_due_date: date | None = None
    notes: str | None = None


class ServiceRead(ServiceBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
