import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import DBBase


class AttendeeStatus(str, enum.Enum):
    """Attendee status enumeration"""

    REGISTERED = "registered"
    WAITLISTED = "waitlisted"
    CANCELLED = "cancelled"


class Attendee(DBBase):
    """Attendee model for event registration with waitlist support"""

    __tablename__ = "attendees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    status = Column(
        Enum(AttendeeStatus),
        nullable=False,
        default=AttendeeStatus.REGISTERED,
        index=True,
    )
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    event = relationship("Event", back_populates="attendees")
    user = relationship("User", back_populates="attendances")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_event_user"),
        Index("ix_attendees_event_status", "event_id", "status"),
    )

    def __repr__(self):
        return f"<Attendee {self.user_id} -> {self.event_id} ({self.status.value})>"
