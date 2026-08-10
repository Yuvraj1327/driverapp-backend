import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class DriverBase(BaseModel):
    license_number: str = Field(min_length=3, max_length=100)
    license_expiry: date | None = None
    address: str | None = None
    emergency_contact: str | None = None


class DriverCreate(DriverBase):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=6, max_length=100)


class DriverUpdate(BaseModel):
    license_number: str | None = None
    license_expiry: date | None = None
    address: str | None = None
    emergency_contact: str | None = None
    is_available: bool | None = None


class DriverRead(DriverBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    is_available: bool
    created_at: datetime
    updated_at: datetime


class DriverWithUser(DriverRead):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
