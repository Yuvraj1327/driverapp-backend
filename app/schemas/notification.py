import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.constants import NotificationType


class NotificationCreate(BaseModel):
    user_id: uuid.UUID
    title: str
    message: str
    notification_type: NotificationType = NotificationType.INFO
    link: str | None = None


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    message: str
    notification_type: NotificationType
    is_read: bool
    link: str | None = None
    created_at: datetime
