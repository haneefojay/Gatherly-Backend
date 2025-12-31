from pydantic import ConfigDict

from app.users.models import UserRole
from app.users.schemas.base import UserBase


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
