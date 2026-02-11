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
    before_state: dict | None = None
    after_state: dict | None = None
    changes: dict | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    endpoint: str | None = None
    method: str | None = None
    status_code: int | None = None
    created_at: datetime

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
                "before_state": {"role": "user"},
                "after_state": {"role": "organizer"},
                "changes": {"role": {"from": "user", "to": "organizer"}},
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "endpoint": "/admin/users/123",
                "method": "PUT",
                "status_code": 200,
                "created_at": "2026-02-07T00:00:00Z",
            }
        }


class PermissionResponse(BaseModel):
    """Admin permission response"""

    id: uuid.UUID
    admin_id: uuid.UUID
    permission: str
    resource_type: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "admin_id": "123e4567-e89b-12d3-a456-426614174001",
                "permission": "user:write",
                "resource_type": "user",
                "created_at": "2026-02-07T00:00:00Z",
            }
        }


class GrantPermissionRequest(BaseModel):
    """Request to grant permission to an admin"""

    admin_id: uuid.UUID
    permission: str = Field(..., description="Permission string (e.g., 'user:write', 'event:delete')")
    resource_type: str | None = Field(None, description="Optional resource type")

    class Config:
        json_schema_extra = {
            "example": {
                "admin_id": "123e4567-e89b-12d3-a456-426614174001",
                "permission": "user:write",
                "resource_type": "user",
            }
        }
