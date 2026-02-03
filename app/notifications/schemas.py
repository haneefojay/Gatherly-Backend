from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from .models import NotificationType


class NotificationBase(BaseModel):
    """Base notification schema"""
    title: str
    message: str
    type: NotificationType
    link: str | None = None


class NotificationCreate(NotificationBase):
    """Schema for creating a notification"""
    user_id: UUID


class NotificationResponse(NotificationBase):
    """Schema for notification response"""
    id: UUID
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationUnreadCount(BaseModel):
    """Schema for unread count response"""
    count: int
