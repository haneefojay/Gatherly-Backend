import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import relationship

from app.core.database import DBBase


class EventStatus(str, enum.Enum):
    """Event status enumeration"""

    DRAFT = "draft"
    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MediaType(str, enum.Enum):
    """Event media type enumeration"""

    IMAGE = "image"
    VIDEO = "video"


event_organizers = Table(
    "event_organizers",
    DBBase.metadata,
    Column("event_id", UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("added_at", DateTime, default=datetime.utcnow, nullable=False),
)


event_tags = Table(
    "event_tags",
    DBBase.metadata,
    Column("event_id", UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Column("added_at", DateTime, default=datetime.utcnow, nullable=False),
)


class Event(DBBase):
    """Event model with full-text search support"""

    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=True, index=True)
    status = Column(
        Enum(EventStatus), nullable=False, default=EventStatus.DRAFT, index=True
    )
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    capacity = Column(Integer, nullable=False, default=100)
    current_attendees = Column(Integer, nullable=False, default=0)
    created_by_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("event_categories.id"), nullable=True, index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    search_vector = Column(TSVECTOR)

    # Core relationships
    created_by = relationship(
        "User", back_populates="created_events", foreign_keys=[created_by_id]
    )
    organizers = relationship(
        "User", secondary=event_organizers, back_populates="organized_events"
    )
    category = relationship("EventCategory", back_populates="events")
    
    # Content relationships
    tags = relationship("EventTag", secondary=event_tags, back_populates="events")
    media = relationship("EventMedia", back_populates="event", cascade="all, delete-orphan")
    
    # Task and attendance relationships
    tasks = relationship("Task", back_populates="event", cascade="all, delete-orphan")
    attendees = relationship(
        "Attendee", back_populates="event", cascade="all, delete-orphan"
    )
    
    # Social relationships
    reviews = relationship("Review", back_populates="event", cascade="all, delete-orphan")
    saved_by = relationship("SavedEvent", back_populates="event", cascade="all, delete-orphan")
    
    # Commerce relationships
    ticket_types = relationship("TicketType", back_populates="event", cascade="all, delete-orphan")

    # Indexes for full-text search and common queries
    __table_args__ = (
        Index("ix_events_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_events_status_start_date", "status", "start_date"),
        Index("ix_events_category_status", "category_id", "status"),
        UniqueConstraint("title", "start_date", "location", name="uq_event_title_date_loc"),
    )

    def __repr__(self):
        return f"<Event {self.title} ({self.status.value})>"

    @property
    def is_full(self) -> bool:
        """Check if event is at capacity"""
        return self.current_attendees >= self.capacity

    @property
    def available_spots(self) -> int:
        """Get number of available spots"""
        return max(0, self.capacity - self.current_attendees)


class EventCategory(DBBase):
    """Event category for organization and filtering"""

    __tablename__ = "event_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(7), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    events = relationship("Event", back_populates="category")

    def __repr__(self):
        return f"<EventCategory {self.name}>"


class EventTag(DBBase):
    """Event tag for flexible categorization"""

    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    events = relationship("Event", secondary=event_tags, back_populates="tags")

    def __repr__(self):
        return f"<EventTag {self.name}>"


class EventMedia(DBBase):
    """Event media (images/videos) with ordering support"""

    __tablename__ = "event_media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    url = Column(String(500), nullable=False)
    type = Column(Enum(MediaType), nullable=False, default=MediaType.IMAGE)
    is_primary = Column(Boolean, default=False, nullable=False)
    order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    event = relationship("Event", back_populates="media")

    __table_args__ = (
        Index("ix_event_media_event_order", "event_id", "order"),
        Index("ix_event_media_event_primary", "event_id", "is_primary"),
    )

    def __repr__(self):
        return f"<EventMedia {self.type.value} for event {self.event_id}>"
