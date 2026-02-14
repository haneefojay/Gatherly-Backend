import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text, Index, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import DBBase


class UserRole(str, enum.Enum):
    """User role enumeration for RBAC"""

    USER = "user"
    ORGANIZER = "organizer"
    ADMIN = "admin"


class UserStatus(str, enum.Enum):
    """User account status enumeration"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class User(DBBase):
    """User model with RBAC support and extended authentication features"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER, index=True)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE, index=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Event relationships
    created_events = relationship(
        "Event", back_populates="created_by", foreign_keys="Event.created_by_id"
    )
    organized_events = relationship(
        "Event", secondary="event_organizers", back_populates="organizers"
    )
    
    # Task and attendance relationships
    assigned_tasks = relationship("Task", back_populates="assignee")
    attendances = relationship("Attendee", back_populates="user")
    
    # Authentication relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    login_history = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")
    email_verifications = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    two_factor_auth = relationship("TwoFactorAuth", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # Profile relationship
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # Preferences relationship
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # Notification relationships
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # Social relationships
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    saved_events = relationship("SavedEvent", back_populates="user", cascade="all, delete-orphan")
    sent_messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    received_messages = relationship("Message", back_populates="receiver", foreign_keys="Message.receiver_id")
    
    # Following relationships (self-referential)
    following = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan"
    )
    followers = relationship(
        "Follow",
        foreign_keys="Follow.following_id",
        back_populates="following",
        cascade="all, delete-orphan"
    )
    
    # Commerce relationships
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    
    # Admin relationships
    admin_audit_logs = relationship("AdminAuditLog", back_populates="admin", cascade="all, delete-orphan")
    
    # Password history
    password_history = relationship("PasswordHistory", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_users_role_status", "role", "status"),
        Index("ix_users_email_verified", "email_verified"),
    )
    
    @property
    def bio(self) -> str | None:
        """Get bio from profile"""
        return self.profile.bio if self.profile else None
    
    @property
    def phone(self) -> str | None:
        """Get phone from profile"""
        return self.profile.phone if self.profile else None
    
    @property
    def location(self) -> str | None:
        """Get location from profile"""
        return self.profile.location if self.profile else None
    
    @property
    def avatar_url(self) -> str | None:
        """Get avatar_url from profile"""
        return self.profile.avatar_url if self.profile else None
    
    @property
    def cover_photo_url(self) -> str | None:
        """Get cover_photo_url from profile"""
        return self.profile.cover_photo_url if self.profile else None
    
    @property
    def social_links(self) -> dict | None:
        """Get social_links from profile"""
        return self.profile.social_links if self.profile else None

    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"


class RefreshToken(DBBase):
    """Refresh token model for JWT token management"""

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    expires_at = Column(DateTime, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_user_expires", "user_id", "expires_at"),
    )

    def __repr__(self):
        return f"<RefreshToken {self.id} for user {self.user_id}>"


class PasswordHistory(DBBase):
    """Track password history to prevent reuse"""

    __tablename__ = "password_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="password_history")

    __table_args__ = (
        Index("ix_password_history_user_created", "user_id", "created_at"),
    )

    def __repr__(self):
        return f"<PasswordHistory for user {self.user_id}>"


class UserProfile(DBBase):
    """Extended user profile information"""

    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    bio = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    location = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    cover_photo_url = Column(String(500), nullable=True)
    social_links = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<UserProfile for user {self.user_id}>"


class UserSession(DBBase):
    """Active user session tracking"""

    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    refresh_token_id = Column(
        UUID(as_uuid=True),
        ForeignKey("refresh_tokens.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    session_token = Column(String(500), unique=True, nullable=False, index=True)
    device_info = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    last_active_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="sessions")
    refresh_token = relationship("RefreshToken", foreign_keys=[refresh_token_id])

    __table_args__ = (
        Index("ix_user_sessions_user_expires", "user_id", "expires_at"),
    )

    def __repr__(self):
        return f"<UserSession {self.id} for user {self.user_id}>"


class LoginHistory(DBBase):
    """Login attempt audit trail"""

    __tablename__ = "login_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="login_history")

    __table_args__ = (
        Index("ix_login_history_user_timestamp", "user_id", "timestamp"),
        Index("ix_login_history_success_timestamp", "success", "timestamp"),
    )

    def __repr__(self):
        status = "✓" if self.success else "✗"
        return f"<LoginHistory {status} {self.user_id} at {self.timestamp}>"


class EmailVerificationToken(DBBase):
    """Email verification token management"""

    __tablename__ = "email_verification_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="email_verifications")

    def __repr__(self):
        return f"<EmailVerificationToken for user {self.user_id}>"


class PasswordResetToken(DBBase):
    """Password reset token management"""

    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="password_resets")

    def __repr__(self):
        return f"<PasswordResetToken for user {self.user_id}>"


class TwoFactorAuth(DBBase):
    """Two-factor authentication settings"""

    __tablename__ = "two_factor_auth"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    secret_key = Column(String(255), nullable=False)
    backup_codes = Column(JSONB, nullable=True)
    enabled = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="two_factor_auth")

    def __repr__(self):
        status = "enabled" if self.enabled else "disabled"
        return f"<TwoFactorAuth {status} for user {self.user_id}>"


class UserPreferences(DBBase):
    """User preferences for theme, language, timezone, etc."""

    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    email_notifications = Column(Boolean, default=True, nullable=False)
    language = Column(String(10), default="en", nullable=False)
    theme = Column(String(10), default="light", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    profile_visibility = Column(String(20), default="public", nullable=False)
    show_attending_events = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreferences for user {self.user_id}>"
