"""Admin authentication and audit routes"""

from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.common.dependencies import get_session
from app.common.permissions import AdminUser
from app.common.exceptions import NotFoundException
from app.users.schemas import TokenResponse
from app.users.services.users import create_access_token, create_refresh_token, record_login_history
from app.admin.schemas import AdminLoginRequest, AuditLogResponse, PermissionResponse, GrantPermissionRequest
from app.admin.services import authenticate_admin, get_audit_logs, log_admin_action
import uuid

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Admin login with mandatory 2FA",
    description="Authenticate admin user (requires 2FA enabled, admin role, valid TOTP code)",
)
async def admin_login(
    credentials: AdminLoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Admin login with mandatory 2FA enforcement"""
    ip_address = request.client.host if request.client else None
    
    admin_user = await authenticate_admin(
        session, 
        credentials.email, 
        credentials.password, 
        credentials.totp_code,
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent")
    )

    access_token = await create_access_token(admin_user)
    refresh_token = await create_refresh_token(session, admin_user)

    await log_admin_action(
        session,
        admin_id=admin_user.id,
        action="login",
        resource_type="admin_session",
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent"),
        endpoint=request.url.path,
        method="POST",
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get(
    "/audit-logs",
    response_model=list[AuditLogResponse],
    summary="Get audit logs",
    description="Retrieve audit logs with optional filters (admin only)",
)
async def list_audit_logs(
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
    admin_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
):
    """Get audit logs with filters"""
    logs = await get_audit_logs(
        session,
        admin_id=uuid.UUID(admin_id) if admin_id else None,
        resource_type=resource_type,
        action=action,
        limit=min(limit, 1000),
    )

    result = await session.execute(
        "SELECT id, email FROM users WHERE id = ANY(:admin_ids)",
        {"admin_ids": [str(log.admin_id) for log in logs]} if logs else {"admin_ids": []},
    )
    admin_emails = {row[0]: row[1] for row in result}

    return [
        AuditLogResponse(
            id=log.id,
            admin_id=log.admin_id,
            admin_email=admin_emails.get(log.admin_id),
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            ip_address=log.ip_address,
            timestamp=log.timestamp,
        )
        for log in logs
    ]


@router.post(
    "/permissions",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant permission to admin",
    description="Grant a specific permission to an admin user (requires admin role)",
)
async def grant_permission(
    request_data: GrantPermissionRequest,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Grant permission to an admin"""
    from app.admin.services import grant_admin_permission
    
    permission = await grant_admin_permission(
        session,
        admin_id=request_data.admin_id,
        permission=request_data.permission,
        resource_type=request_data.resource_type,
        granted_by_id=admin_user.id
    )
    
    return permission


@router.delete(
    "/permissions/{admin_id}/{permission}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke permission from admin",
    description="Revoke a specific permission from an admin user (requires admin role)",
)
async def revoke_permission(
    admin_id: str,
    permission: str,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
    resource_type: Optional[str] = None,
):
    """Revoke permission from an admin"""
    from app.admin.services import revoke_admin_permission
    
    revoked = await revoke_admin_permission(
        session,
        admin_id=uuid.UUID(admin_id),
        permission=permission,
        resource_type=resource_type
    )
    
    if not revoked:
        raise NotFoundException("Permission not found")


@router.get(
    "/permissions/{admin_id}",
    response_model=list[PermissionResponse],
    summary="Get admin permissions",
    description="Get all permissions for a specific admin (requires admin role)",
)
async def list_admin_permissions(
    admin_id: str,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Get all permissions for an admin"""
    from app.admin.services import get_admin_permissions
    
    permissions = await get_admin_permissions(session, uuid.UUID(admin_id))
    return permissions
