from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from app.users.models import UserRole
from app.users.schemas.base import UserBase


class UserResponse(UserBase):
    """User response schema"""

    id: UUID
    username: str | None = None
    role: UserRole
    is_active: bool
    email_verified: bool
    
    # Profile fields
    bio: str | None = None
    phone: str | None = None
    location: str | None = None
    avatar_url: str | None = None
    social_links: dict | None = None
    job_title: str | None = None
    
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
                "role": "user",
                "is_active": True,
                "email_verified": True,
                "bio": "Event organizer and tech enthusiast",
                "phone": "+1234567890",
                "location": "San Francisco, CA",
                "avatar_url": "/uploads/avatars/user-id/avatar.jpg",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
        },
    )
