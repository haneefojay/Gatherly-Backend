from pydantic import ConfigDict, field_validator

from app.users.models import UserRole
from app.users.schemas.base import UserBase


class UserCreate(UserBase):
    """User creation schema"""

    password: str
    role: UserRole = UserRole.USER

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: UserRole) -> UserRole:
        """Prevent users from registering with admin role"""
        if value == UserRole.ADMIN:
            raise ValueError("Cannot register with admin role")
        return value

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
