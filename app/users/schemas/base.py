"""User schemas for request/response validation"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.users.models import UserRole


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    """User creation schema"""

    password: str
    role: UserRole = UserRole.USER

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe",
                "password": "SecurePass123!",
                "role": "user",
            }
        },
    )


class UserUpdate(BaseModel):
    """User update schema"""

    full_name: str | None = None
    email: EmailStr | None = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "full_name": "Jane Doe",
                "email": "jane@example.com",
            }
        },
    )


class UserResponse(UserBase):
    """User response schema"""

    id: UUID
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "role": "user",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
        },
    )


class UserRoleUpdate(BaseModel):
    """Schema for updating user role (Admin only)"""

    role: UserRole

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"role": "organizer"}},
    )
