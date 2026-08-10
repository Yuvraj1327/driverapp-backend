import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.constants import RoleName


class UserBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=100)
    role: RoleName = RoleName.DRIVER


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = None
    is_active: bool | None = None
    role: RoleName | None = None


class UserChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=100)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    is_active: bool
    role_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class UserWithRole(UserRead):
    role_name: str | None = None
