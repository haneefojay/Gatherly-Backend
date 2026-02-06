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
    Text,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import DBBase


class MessageStatus(str, enum.Enum):
    """Message status enumeration"""

    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


class Review(DBBase):
    """Event review by users"""

    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    rating = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    helpful_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    event = relationship("Event", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
    comments = relationship("Comment", back_populates="review", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
        CheckConstraint("helpful_count >= 0", name="check_helpful_count_positive"),
        UniqueConstraint("event_id", "user_id", name="uq_review_event_user"),
        Index("ix_reviews_event_created", "event_id", "created_at"),
        Index("ix_reviews_event_rating", "event_id", "rating"),
    )

    def __repr__(self):
        return f"<Review {self.rating}⭐ by user {self.user_id}>"


class Comment(DBBase):
    """Comment on reviews with threading support"""

    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    parent_comment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    review = relationship("Review", back_populates="comments")
    user = relationship("User", back_populates="comments")
    parent_comment = relationship("Comment", remote_side=[id], backref="replies")

    __table_args__ = (
        Index("ix_comments_review_created", "review_id", "created_at"),
        Index("ix_comments_parent", "parent_comment_id"),
    )

    def __repr__(self):
        return f"<Comment by user {self.user_id}>"


class SavedEvent(DBBase):
    """User's saved/bookmarked events"""

    __tablename__ = "saved_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    saved_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="saved_events")
    event = relationship("Event", back_populates="saved_by")

    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_saved_event_user_event"),
        Index("ix_saved_events_user_saved", "user_id", "saved_at"),
    )

    def __repr__(self):
        return f"<SavedEvent user {self.user_id} -> event {self.event_id}>"


class Follow(DBBase):
    """User following relationship"""

    __tablename__ = "follows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    follower_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    following_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    followed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    following = relationship("User", foreign_keys=[following_id], back_populates="followers")

    __table_args__ = (
        CheckConstraint("follower_id != following_id", name="check_no_self_follow"),
        UniqueConstraint("follower_id", "following_id", name="uq_follow_follower_following"),
        Index("ix_follows_follower", "follower_id"),
        Index("ix_follows_following", "following_id"),
    )

    def __repr__(self):
        return f"<Follow {self.follower_id} -> {self.following_id}>"


class Message(DBBase):
    """Direct message between users"""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    receiver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content = Column(Text, nullable=False)
    status = Column(Enum(MessageStatus), nullable=False, default=MessageStatus.SENT, index=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")

    __table_args__ = (
        Index("ix_messages_sender_created", "sender_id", "created_at"),
        Index("ix_messages_receiver_read", "receiver_id", "read_at"),
        Index("ix_messages_receiver_status", "receiver_id", "status"),
    )

    def __repr__(self):
        return f"<Message from {self.sender_id} to {self.receiver_id} ({self.status.value})>"
