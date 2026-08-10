import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import ExpenseStatus


class ExpenseBase(BaseModel):
    vehicle_id: uuid.UUID
    driver_id: uuid.UUID
    category_id: uuid.UUID
    amount: float = Field(gt=0)
    expense_date: date = Field(default_factory=date.today)
    description: str | None = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    expense_date: date | None = None
    description: str | None = None
    category_id: uuid.UUID | None = None


class ExpenseRead(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    receipt_url: str | None = None
    status: ExpenseStatus
    created_at: datetime
    updated_at: datetime


class ExpenseApprovalAction(BaseModel):
    decision: ExpenseStatus
    remarks: str | None = None
