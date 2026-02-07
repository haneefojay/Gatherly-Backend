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
from app.users.services.users import authenticate_user
from app.users.services.twofa import check_user_2fa_enabled, verify_two_factor_code
from app.admin.models import AdminAuditLog


async def authenticate_admin(
    session: AsyncSession, email: str, password: str, totp_code: Optional[str] = None
) -> User:
    """Authenticate admin user with mandatory 2FA
    
    Args:
        session: Database session
        email: Admin email
        password: Admin password
        totp_code: TOTP code (required for admins)
        
    Returns:
        Admin user instance
        
    Raises:
        UnauthorizedException: If authentication fails or user is not admin
    """
    user = await authenticate_user(session, email, password)
    
    if not user:
        raise UnauthorizedException("Invalid credentials")
    
    if user.role != UserRole.ADMIN:
        raise UnauthorizedException("Admin access required")
    
    has_2fa = await check_user_2fa_enabled(session, user.id)
    
    if not has_2fa:
        raise UnauthorizedException("Admin accounts must have 2FA enabled")
    
    if not totp_code:
        raise UnauthorizedException("Two-factor authentication code required")
    
    if not await verify_two_factor_code(session, user, totp_code):
        raise UnauthorizedException("Invalid two-factor authentication code")
    
    return user


async def log_admin_action(
    session: AsyncSession,
    admin_id: uuid.UUID,
    action: str,
    resource_type: str,
    resource_id: Optional[uuid.UUID] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> AdminAuditLog:
    """Log admin action to audit trail
    
    Args:
        session: Database session
        admin_id: Admin user ID
        action: Action performed (e.g., "create", "update", "delete")
        resource_type: Type of resource (e.g., "user", "event", "setting")
        resource_id: ID of affected resource
        details: Additional details about the action
        ip_address: IP address of admin
        
    Returns:
        Created audit log entry
    """
    audit_log = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        timestamp=datetime.utcnow(),
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
    
    query = query.order_by(AdminAuditLog.timestamp.desc()).limit(limit)
    
    result = await session.execute(query)
    return list(result.scalars().all())
