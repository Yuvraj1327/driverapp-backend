import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExpenseCategoryBase(BaseModel):
    name: str
    description: str | None = None


class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass


class ExpenseCategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ExpenseCategoryRead(ExpenseCategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
