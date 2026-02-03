import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import DBBase


class NotificationType(str, enum.Enum):
    """Notification type enumeration"""
    TASK_ASSIGNED = "task_assigned"
    EVENT_STATUS_CHANGE = "event_status_change"
    REGISTRATION_UPDATE = "registration_update"
    GENERAL = "general"


class Notification(DBBase):
    """In-app notification model"""

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type = Column(Enum(NotificationType), nullable=False, default=NotificationType.GENERAL)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(255), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.id} for user {self.user_id} ({self.type.value})>"
