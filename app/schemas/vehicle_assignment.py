import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import AssignmentStatus


class AssignmentCreate(BaseModel):
    vehicle_id: uuid.UUID
    driver_id: uuid.UUID
    assigned_date: date = Field(default_factory=date.today)
    notes: str | None = None


class AssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vehicle_id: uuid.UUID
    driver_id: uuid.UUID
    assigned_date: date
    unassigned_date: date | None = None
    status: AssignmentStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
