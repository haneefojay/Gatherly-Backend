"""Admin authentication and audit logging services"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import (
    UnauthorizedException,
)
from app.users.models import User, UserRole
from app.users.services.users import authenticate_user, record_login_history
from app.users.services.twofa import check_user_2fa_enabled, verify_two_factor_code
from app.admin.models import AdminAuditLog


async def authenticate_admin(
    session: AsyncSession, 
    email: str, 
    password: str, 
    totp_code: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> User:
    """Authenticate admin user with mandatory 2FA and optional IP whitelist
    
    Args:
        session: Database session
        email: Admin email
        password: Admin password
        totp_code: TOTP code (required for admins)
        ip_address: IP address of the request
        user_agent: User agent of the request
        
    Returns:
        Admin user instance
        
    Raises:
        UnauthorizedException: If authentication fails or user is not admin
    """
    from app.admin.models import AdminSetting
    
    user = await authenticate_user(session, email, password)
    
    if not user:
        # Check if user exists to log failure
        result = await session.execute(select(User).where(User.email == email))
        potential_user = result.scalar_one_or_none()
        if potential_user:
            await record_login_history(
                session, 
                potential_user.id, 
                success=False, 
                ip_address=ip_address, 
                user_agent=user_agent,
                failure_reason="Invalid credentials"
            )
            await session.commit()
        raise UnauthorizedException("Invalid credentials")
    
    if user.role != UserRole.ADMIN:
        await record_login_history(
            session, 
            user.id, 
            success=False, 
            ip_address=ip_address, 
            user_agent=user_agent,
            failure_reason="Admin access required (User is not admin)"
        )
        await session.commit()
        raise UnauthorizedException("Admin access required")
    
    if ip_address:
        result = await session.execute(
            select(AdminSetting).where(AdminSetting.key == "admin_ip_whitelist")
        )
        whitelist_setting = result.scalar_one_or_none()
        
        if whitelist_setting and whitelist_setting.value.get("enabled"):
            allowed_ips = whitelist_setting.value.get("ips", [])
            if allowed_ips and ip_address not in allowed_ips:
                await record_login_history(
                    session, 
                    user.id, 
                    success=False, 
                    ip_address=ip_address, 
                    user_agent=user_agent,
                    failure_reason="IP address not whitelisted"
                )
                await session.commit()
                raise UnauthorizedException(f"IP address {ip_address} not whitelisted for admin access")
    
    has_2fa = await check_user_2fa_enabled(session, user.id)
    
    if not has_2fa:
        await record_login_history(
            session, 
            user.id, 
            success=False, 
            ip_address=ip_address, 
            user_agent=user_agent,
            failure_reason="2FA mandatory for admin"
        )
        await session.commit()
        raise UnauthorizedException("Admin accounts must have 2FA enabled")
    
    if not totp_code:
        await record_login_history(
            session, 
            user.id, 
            success=False, 
            ip_address=ip_address, 
            user_agent=user_agent,
            failure_reason="2FA code required"
        )
        await session.commit()
        raise UnauthorizedException("Two-factor authentication code required")
    
    if not await verify_two_factor_code(session, user, totp_code):
        await record_login_history(
            session, 
            user.id, 
            success=False, 
            ip_address=ip_address, 
            user_agent=user_agent,
            failure_reason="Invalid 2FA code"
        )
        await session.commit()
        raise UnauthorizedException("Invalid two-factor authentication code")
    
    # Finally, record successful login
    await record_login_history(
        session, 
        user.id, 
        success=True, 
        ip_address=ip_address, 
        user_agent=user_agent
    )
    # The caller will commit in admin_login
    
    return user


async def log_admin_action(
    session: AsyncSession,
    admin_id: uuid.UUID,
    action: str,
    resource_type: str,
    resource_id: Optional[uuid.UUID] = None,
    before_state: Optional[dict] = None,
    after_state: Optional[dict] = None,
    changes: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
) -> AdminAuditLog:
    """Log admin action to audit trail
    
    Args:
        session: Database session
        admin_id: Admin user ID
        action: Action performed (e.g., "create", "update", "delete")
        resource_type: Type of resource (e.g., "user", "event", "setting")
        resource_id: ID of affected resource
        before_state: Resource state before change
        after_state: Resource state after change
        changes: Specific fields that changed
        ip_address: IP address of admin
        user_agent: User agent string
        endpoint: API endpoint accessed
        method: HTTP method
        status_code: HTTP status code
        
    Returns:
        Created audit log entry
    """
    audit_log = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        before_state=before_state,
        after_state=after_state,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
    )
    
    session.add(audit_log)
    await session.commit()
    await session.refresh(audit_log)
    
    return audit_log


async def get_audit_logs(
    session: AsyncSession,
    admin_id: Optional[uuid.UUID] = None,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
) -> list[AdminAuditLog]:
    """Get audit logs with filters
    
    Args:
        session: Database session
        admin_id: Filter by admin user
        resource_type: Filter by resource type
        action: Filter by action type
        limit: Maximum number of logs to return
        
    Returns:
        List of audit log entries
    """
    query = select(AdminAuditLog)
    
    if admin_id:
        query = query.where(AdminAuditLog.admin_id == admin_id)
    
    if resource_type:
        query = query.where(AdminAuditLog.resource_type == resource_type)
    
    if action:
        query = query.where(AdminAuditLog.action == action)
    
    query = query.order_by(AdminAuditLog.created_at.desc()).limit(limit)
    
    result = await session.execute(query)
    return list(result.scalars().all())


async def check_admin_permission(
    session: AsyncSession,
    admin_id: uuid.UUID,
    permission: str,
    resource_type: Optional[str] = None
) -> bool:
    """Check if admin has specific permission
    
    Args:
        session: Database session
        admin_id: Admin user ID
        permission: Permission to check (e.g., "user:write", "event:delete")
        resource_type: Optional resource type filter
        
    Returns:
        True if admin has permission, False otherwise
    """
    from app.admin.models import AdminPermission
    
    query = select(AdminPermission).where(
        AdminPermission.admin_id == admin_id,
        AdminPermission.permission == permission
    )
    
    if resource_type:
        query = query.where(
            (AdminPermission.resource_type == resource_type) | 
            (AdminPermission.resource_type == None)
        )
    
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None


async def grant_admin_permission(
    session: AsyncSession,
    admin_id: uuid.UUID,
    permission: str,
    resource_type: Optional[str] = None,
    granted_by_id: Optional[uuid.UUID] = None
) -> "AdminPermission":
    """Grant permission to an admin
    
    Args:
        session: Database session
        admin_id: Admin user ID to grant permission to
        permission: Permission to grant
        resource_type: Optional resource type
        granted_by_id: ID of admin granting the permission
        
    Returns:
        Created permission record
    """
    from app.admin.models import AdminPermission
    
    result = await session.execute(
        select(AdminPermission).where(
            AdminPermission.admin_id == admin_id,
            AdminPermission.permission == permission,
            AdminPermission.resource_type == resource_type
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return existing
    
    permission_record = AdminPermission(
        admin_id=admin_id,
        permission=permission,
        resource_type=resource_type,
        created_by_id=granted_by_id
    )
    
    session.add(permission_record)
    await session.commit()
    await session.refresh(permission_record)
    
    return permission_record


async def revoke_admin_permission(
    session: AsyncSession,
    admin_id: uuid.UUID,
    permission: str,
    resource_type: Optional[str] = None
) -> bool:
    """Revoke permission from an admin
    
    Args:
        session: Database session
        admin_id: Admin user ID
        permission: Permission to revoke
        resource_type: Optional resource type
        
    Returns:
        True if permission was revoked, False if not found
    """
    from app.admin.models import AdminPermission
    from sqlalchemy import delete
    
    query = delete(AdminPermission).where(
        AdminPermission.admin_id == admin_id,
        AdminPermission.permission == permission
    )
    
    if resource_type:
        query = query.where(AdminPermission.resource_type == resource_type)
    
    result = await session.execute(query)
    await session.commit()
    
    return result.rowcount > 0


async def get_admin_permissions(
    session: AsyncSession,
    admin_id: uuid.UUID
) -> list["AdminPermission"]:
    """Get all permissions for an admin
    
    Args:
        session: Database session
        admin_id: Admin user ID
        
    Returns:
        List of permission records
    """
    from app.admin.models import AdminPermission
    
    result = await session.execute(
        select(AdminPermission).where(AdminPermission.admin_id == admin_id)
    )
    return list(result.scalars().all())
