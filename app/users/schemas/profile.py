"""Profile management schemas"""

from pydantic import BaseModel, EmailStr, Field


class ProfileUpdate(BaseModel):
    """Profile update request schema"""

    full_name: str | None = Field(None, min_length=1, max_length=255)
    username: str | None = Field(None, min_length=3, max_length=100)
    bio: str | None = Field(None, max_length=500)
    job_title: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    location: str | None = Field(None, max_length=255)
    social_links: dict | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "John Doe",
                "username": "johndoe",
                "bio": "Event organizer and tech enthusiast",
                "phone": "+1234567890",
                "location": "San Francisco, CA",
            }
        }


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePass456!",
            }
        }


class UserPreferences(BaseModel):
    """User preferences schema"""

    language: str
    theme: str
    timezone: str
    currency: str
    is_profile_public: bool = True
    allow_search_indexing: bool = False
    show_email: bool = False
    show_phone: bool = False
    attendance_visibility: str = "Friends & Connections"
    past_events_visible: bool = True
    share_data_third_party: bool = False
    share_analytics: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "language": "en-US",
                "theme": "dark",
                "timezone": "America/Los_Angeles",
                "currency": "USD",
                "is_profile_public": True,
                "allow_search_indexing": False,
                "show_email": False,
                "show_phone": False,
                "attendance_visibility": "Friends & Connections",
                "past_events_visible": True,
                "share_data_third_party": False,
                "share_analytics": True,
            }
        }


class UserPreferencesUpdate2(BaseModel):
    """User preferences update request schema"""

    language: str | None = None
    theme: str | None = None
    timezone: str | None = None
    currency: str | None = None
    is_profile_public: bool | None = None
    allow_search_indexing: bool | None = None
    show_email: bool | None = None
    show_phone: bool | None = None
    attendance_visibility: str | None = None
    past_events_visible: bool | None = None
    share_data_third_party: bool | None = None
    share_analytics: bool | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "language": "es-ES",
                "theme": "light",
            }
        }


class SessionResponse(BaseModel):
    """User session response schema"""

    id: str
    device_info: str | None = None
    ip_address: str | None = None
    last_active_at: str
    created_at: str
    is_current: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc123-session-id",
                "device_info": "Chrome on Windows 10",
                "ip_address": "192.168.1.1",
                "last_active_at": "2026-02-06T22:00:00Z",
                "created_at": "2026-02-05T10:00:00Z",
                "is_current": False,
            }
        }
