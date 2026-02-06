import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, UniqueConstraint, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import DBBase


class AttendeeStatus(str, enum.Enum):
    """Attendee status enumeration"""

    REGISTERED = "registered"
    WAITLISTED = "waitlisted"
    CANCELLED = "cancelled"
    CHECKED_IN = "checked_in"


class WaitlistStatus(str, enum.Enum):
    """Waitlist entry status enumeration"""

    PENDING = "pending"
    INVITED = "invited"
    CONVERTED = "converted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Attendee(DBBase):
    """Attendee model for event registration with ticketing links"""

    __tablename__ = "attendees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ticket_type_id = Column(
        UUID(as_uuid=True), ForeignKey("ticket_types.id", ondelete="SET NULL"), nullable=True, index=True
    )
    order_item_id = Column(
        UUID(as_uuid=True), ForeignKey("order_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status = Column(
        Enum(AttendeeStatus),
        nullable=False,
        default=AttendeeStatus.REGISTERED,
        index=True,
    )
    checked_in_at = Column(DateTime, nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    event = relationship("Event", back_populates="attendees")
    user = relationship("User", back_populates="attendances")
    ticket_type = relationship("TicketType", foreign_keys=[ticket_type_id])
    order_item = relationship("OrderItem", foreign_keys=[order_item_id])

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_event_user"),
        Index("ix_attendees_event_status", "event_id", "status"),
        Index("ix_attendees_registered_at", "registered_at"),
    )

    def __repr__(self):
        return f"<Attendee {self.user_id} -> {self.event_id} ({self.status.value})>"


class Waitlist(DBBase):
    """Waitlist model for advanced event queue management"""

    __tablename__ = "waitlists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ticket_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ticket_types.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    priority = Column(Integer, default=0, nullable=False)
    status = Column(
        Enum(WaitlistStatus),
        nullable=False,
        default=WaitlistStatus.PENDING,
        index=True
    )
    invited_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    event = relationship("Event")
    user = relationship("User")
    ticket_type = relationship("TicketType")

    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_waitlist_event_user"),
        Index("ix_waitlist_event_priority", "event_id", "priority"),
        Index("ix_waitlist_status_expires", "status", "expires_at"),
    )

    def __repr__(self):
        return f"<Waitlist user {self.user_id} for event {self.event_id} status {self.status.value}>"
