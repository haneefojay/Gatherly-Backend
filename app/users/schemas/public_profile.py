"""Schemas for public profiles, preferences, stats, and activity"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PublicProfileResponse(BaseModel):
    """Public-facing user profile"""

    id: UUID
    username: str | None = None
    full_name: str
    bio: str | None = None
    location: str | None = None
    avatar_url: str | None = None
    cover_photo_url: str | None = None
    social_links: dict | None = None
    events_organized_count: int = 0
    events_attended_count: int = 0
    member_since: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPreferencesResponse(BaseModel):
    """User preferences response"""

    email_notifications: bool = True
    language: str = "en"
    theme: str = "light"
    timezone: str = "UTC"
    currency: str = "USD"
    profile_visibility: str = "public"
    show_attending_events: bool = True

    model_config = ConfigDict(from_attributes=True)


class UserPreferencesUpdate(BaseModel):
    """User preferences update request"""

    email_notifications: bool | None = None
    language: str | None = Field(None, max_length=10)
    theme: str | None = Field(None, pattern="^(light|dark|system)$")
    timezone: str | None = Field(None, max_length=50)
    currency: str | None = Field(None, min_length=3, max_length=3)
    profile_visibility: str | None = Field(None, pattern="^(public|private)$")
    show_attending_events: bool | None = None


class UserStatsResponse(BaseModel):
    """User statistics"""

    events_organized: int = 0
    events_attended: int = 0
    reviews_given: int = 0
    reviews_received: int = 0
    saved_events_count: int = 0


class UserActivityItem(BaseModel):
    """Single activity entry"""

    type: str
    title: str
    description: str
    timestamp: datetime
    event_id: UUID | None = None
    event_title: str | None = None


class UserActivityResponse(BaseModel):
    """Paginated activity timeline"""

    items: list[UserActivityItem]
    total: int
