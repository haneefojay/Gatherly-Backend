"""Admin authentication schemas"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import uuid


class AdminLoginRequest(BaseModel):
    """Admin login request with mandatory 2FA"""

    email: EmailStr
    password: str
    totp_code: str = Field(..., min_length=6, max_length=6, description="2FA code (required for admins)")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@gatherly.com",
                "password": "AdminPass123!",
                "totp_code": "123456",
            }
        }


class AuditLogResponse(BaseModel):
    """Audit log entry response"""

    id: uuid.UUID
    admin_id: uuid.UUID
    admin_email: str | None = None
    action: str
    resource_type: str
    resource_id: uuid.UUID | None = None
    details: dict
    ip_address: str | None = None
    timestamp: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "admin_id": "123e4567-e89b-12d3-a456-426614174001",
                "admin_email": "admin@gatherly.com",
                "action": "update",
                "resource_type": "user",
                "resource_id": "123e4567-e89b-12d3-a456-426614174002",
                "details": {"role": "organizer"},
                "ip_address": "192.168.1.1",
                "timestamp": "2026-02-07T00:00:00Z",
            }
        }
