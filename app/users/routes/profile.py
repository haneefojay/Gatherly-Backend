"""Profile management routes"""

from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_session
from app.common.permissions import CurrentUser
from app.users.schemas import (
    ProfileUpdate,
    ChangePasswordRequest,
    SessionResponse,
    UserResponse,
)
from app.users.services.profile import (
    update_user_profile,
    change_user_password,
    get_user_sessions,
    revoke_user_session,
)
import uuid

router = APIRouter()


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update profile information (name, username, bio, phone, location)",
)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Update user profile"""
    user = await update_user_profile(session, current_user, profile_data)
    return user


@router.put(
    "/me/password",
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change user password (requires current password)",
)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Change user password"""
    await change_user_password(
        session,
        current_user,
        password_data.current_password,
        password_data.new_password,
    )
    return {"message": "Password changed successfully"}


@router.get(
    "/me/sessions",
    response_model=list[SessionResponse],
    summary="Get active sessions",
    description="List all active sessions for the current user",
)
async def list_sessions(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Get all active user sessions"""
    sessions = await get_user_sessions(session, current_user.id)
    return sessions


@router.delete(
    "/me/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke session",
    description="Revoke a specific session (logout from that device)",
)
async def revoke_session(
    session_id: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Revoke a specific user session"""
    await revoke_user_session(session, current_user.id, uuid.UUID(session_id))
    return None


@router.post(
    "/me/avatar",
    status_code=status.HTTP_200_OK,
    summary="Upload avatar",
    description="Upload user avatar image",
)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(),
    session: AsyncSession = Depends(get_session),
):
    """Upload user avatar (placeholder - implement with storage service)"""
    return {
        "message": "Avatar upload endpoint ready - integrate with storage service (S3/Azure Blob)",
        "filename": file.filename,
        "content_type": file.content_type,
    }
