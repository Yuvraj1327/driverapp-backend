import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.constants import ExpenseStatus


class ExpenseApprovalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    expense_id: uuid.UUID
    reviewer_id: uuid.UUID | None = None
    decision: ExpenseStatus
    remarks: str | None = None
    created_at: datetime
