from pydantic import BaseModel, ConfigDict, EmailStr

from app.users.models import UserRole


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


class UserRoleUpdate(BaseModel):
    """Schema for updating user role (Admin only)"""

    role: UserRole

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"role": "organizer"}},
    )
