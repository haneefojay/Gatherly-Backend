"""Admin user management routes"""

import math
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_session
from app.common.permissions import AdminUser
from app.admin.schemas.admin_users import (
    AdminUserListItem,
    AdminUserListResponse,
    AdminUserDetailResponse,
    AdminUserUpdateRequest,
    SuspendUserRequest,
    BanUserRequest,
    AdminNoteCreate,
    AdminNoteResponse,
    AdminUserStatsResponse,
    UserGrowthResponse,
    BulkActionRequest,
    BulkActionResponse,
)
from app.admin.services.admin_users import (
    list_users,
    get_user_detail,
    update_user,
    suspend_user,
    ban_user,
    unsuspend_user,
    verify_user,
    soft_delete_user,
    export_user_data,
    admin_reset_password,
    create_impersonation,
    add_admin_note,
    delete_admin_note,
    revoke_user_session,
    revoke_all_user_sessions,
)
from app.admin.services.admin_analytics import get_user_stats, get_user_growth
from app.admin.services.admin_bulk import execute_bulk_action
from app.external.email import email_service

router = APIRouter()


@router.get(
    "/",
    response_model=AdminUserListResponse,
    summary="List all users",
    description="Paginated user list with advanced filtering, search, and sort",
)
async def list_all_users(
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None, pattern="^(user|organizer|admin)$"),
    user_status: Optional[str] = Query(None, alias="status", pattern="^(active|suspended|banned|pending|deleted)$"),
    email_verified: Optional[bool] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    last_login_after: Optional[datetime] = None,
    last_login_before: Optional[datetime] = None,
    location: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|email|full_name|last_login_at|role|status)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    """List users with advanced filtering"""
    users, total = await list_users(
        session,
        page=page,
        page_size=page_size,
        role=role,
        status=user_status,
        email_verified=email_verified,
        search=search,
        date_from=date_from,
        date_to=date_to,
        last_login_after=last_login_after,
        last_login_before=last_login_before,
        location=location,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return AdminUserListResponse(
        users=[AdminUserListItem.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get(
    "/stats",
    response_model=AdminUserStatsResponse,
    summary="Get user statistics",
    description="Aggregated user analytics: counts, rates, DAU/WAU/MAU",
)
async def get_stats(
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Get user analytics dashboard"""
    return await get_user_stats(session)


@router.get(
    "/growth",
    response_model=UserGrowthResponse,
    summary="Get user growth data",
    description="Daily user registration counts for growth charts",
)
async def get_growth(
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
    days: int = Query(30, ge=7, le=365),
):
    """Get user growth chart data"""
    return await get_user_growth(session, days=days)


@router.post(
    "/bulk-action",
    response_model=BulkActionResponse,
    summary="Execute bulk action",
    description="Perform bulk operations (suspend, verify, export, email) on multiple users",
)
async def bulk_action(
    data: BulkActionRequest,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Execute bulk action on users"""
    return await execute_bulk_action(
        session,
        admin=admin_user,
        action=data.action,
        user_ids=data.user_ids,
        reason=data.reason,
    )


@router.get(
    "/{user_id}",
    response_model=AdminUserDetailResponse,
    summary="Get user detail",
    description="Complete user details including profile, 2FA, logins, sessions, events, reviews, notes",
)
async def get_user(
    user_id: UUID,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Get complete user detail"""
    return await get_user_detail(session, user_id)


@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Update user",
    description="Update user information (name, email, role, verification) with audit trail",
)
async def update_user_endpoint(
    user_id: UUID,
    data: AdminUserUpdateRequest,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Update user information"""
    update_data = data.model_dump(exclude_unset=True)
    user = await update_user(session, admin_user, user_id, update_data)
    return {"message": "User updated successfully", "user_id": str(user.id)}


@router.post(
    "/{user_id}/suspend",
    status_code=status.HTTP_200_OK,
    summary="Suspend user",
    description="Suspend account, invalidate sessions, log action",
)
async def suspend_user_endpoint(
    user_id: UUID,
    data: SuspendUserRequest,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Suspend a user account"""
    user = await suspend_user(session, admin_user, user_id, data.reason, data.duration_days)
    return {"message": "User suspended", "user_id": str(user.id), "status": user.status.value}


@router.post(
    "/{user_id}/ban",
    status_code=status.HTTP_200_OK,
    summary="Ban user",
    description="Permanently ban account, invalidate sessions, log action",
)
async def ban_user_endpoint(
    user_id: UUID,
    data: BanUserRequest,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Ban a user account"""
    user = await ban_user(session, admin_user, user_id, data.reason)
    return {"message": "User banned", "user_id": str(user.id), "status": user.status.value}


@router.post(
    "/{user_id}/unsuspend",
    status_code=status.HTTP_200_OK,
    summary="Unsuspend user",
    description="Restore suspended/banned account, log action",
)
async def unsuspend_user_endpoint(
    user_id: UUID,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Restore a suspended user"""
    user = await unsuspend_user(session, admin_user, user_id)
    return {"message": "User restored", "user_id": str(user.id), "status": user.status.value}


@router.post(
    "/{user_id}/verify",
    status_code=status.HTTP_200_OK,
    summary="Verify user",
    description="Manually verify user email, log action",
)
async def verify_user_endpoint(
    user_id: UUID,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Manually verify a user"""
    user = await verify_user(session, admin_user, user_id)
    return {"message": "User verified", "user_id": str(user.id), "email_verified": user.email_verified}


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete user (GDPR)",
    description="Soft delete with data anonymization (GDPR compliant)",
)
async def delete_user_endpoint(
    user_id: UUID,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Soft delete user (GDPR compliant)"""
    await soft_delete_user(session, admin_user, user_id)
    return {"message": "User deleted and data anonymized"}


@router.post(
    "/{user_id}/export-data",
    status_code=status.HTTP_200_OK,
    summary="Export user data (GDPR)",
    description="Export all user data for GDPR data portability request",
)
async def export_data_endpoint(
    user_id: UUID,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Export all user data"""
    data = await export_user_data(session, user_id)
    return data


@router.post(
    "/{user_id}/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset user password",
    description="Generate password reset token and send reset email",
)
async def reset_password_endpoint(
    user_id: UUID,
    admin_user: AdminUser,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """Admin-initiated password reset"""
    user, token = await admin_reset_password(session, admin_user, user_id)
    
    background_tasks.add_task(
        email_service.send_password_reset_email, 
        user.email, 
        token, 
        user.full_name
    )
    
    return {"message": "Password reset token generated and email sent", "reset_token": token}


@router.post(
    "/{user_id}/impersonate",
    status_code=status.HTTP_200_OK,
    summary="Impersonate user",
    description="Create time-limited (30 min) impersonation session with full audit trail",
)
async def impersonate_user_endpoint(
    user_id: UUID,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Create impersonation session"""
    return await create_impersonation(session, admin_user, user_id)


@router.post(
    "/{user_id}/notes",
    response_model=AdminNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add admin note",
    description="Add a note to user's account (visible only to admins)",
)
async def add_note_endpoint(
    user_id: UUID,
    data: AdminNoteCreate,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Add admin note to user"""
    note = await add_admin_note(session, admin_user, user_id, data.content)
    return AdminNoteResponse(
        id=note.id,
        admin_email=admin_user.email,
        content=note.content,
        created_at=note.created_at,
    )


@router.delete(
    "/{user_id}/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete admin note",
    description="Delete an admin note from a user account",
)
async def delete_note_endpoint(
    user_id: UUID,
    note_id: UUID,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Delete admin note"""
    await delete_admin_note(session, admin_user, user_id, note_id)


@router.delete(
    "/{user_id}/sessions",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke all user sessions",
    description="Terminate all active sessions and revoke all refresh tokens for a user",
)
async def revoke_all_sessions_endpoint(
    user_id: UUID,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Revoke all active sessions for a user"""
    await revoke_all_user_sessions(session, admin_user, user_id)


@router.delete(
    "/{user_id}/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke specific user session",
    description="Terminate a specific active session for a user",
)
async def revoke_session_endpoint(
    user_id: UUID,
    session_id: UUID,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Revoke a specific user session"""
    await revoke_user_session(session, admin_user, user_id, session_id)
