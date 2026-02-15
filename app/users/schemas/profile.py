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
