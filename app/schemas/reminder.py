import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.core.constants import ReminderStatus, ReminderType


class ReminderBase(BaseModel):
    vehicle_id: uuid.UUID | None = None
    driver_id: uuid.UUID | None = None
    reminder_type: ReminderType
    title: str
    description: str | None = None
    due_date: date


class ReminderCreate(ReminderBase):
    pass


class ReminderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: date | None = None
    status: ReminderStatus | None = None


class ReminderRead(ReminderBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: ReminderStatus
    created_at: datetime
    updated_at: datetime
