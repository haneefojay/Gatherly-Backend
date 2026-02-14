"""Profile management routes"""

from fastapi import APIRouter, Depends, Query, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_session
from app.common.permissions import CurrentUser
from app.users.schemas import (
    ProfileUpdate,
    ChangePasswordRequest,
    SessionResponse,
    UserResponse,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserStatsResponse,
    UserActivityResponse,
)
from app.users.services.profile import (
    update_user_profile,
    change_user_password,
    get_user_sessions,
    revoke_user_session,
)
from app.users.services.avatar import upload_user_avatar, delete_user_avatar, upload_cover_photo, delete_cover_photo
from app.users.services.preferences import get_user_preferences, update_user_preferences
from app.users.services.activity import get_user_stats, get_user_activity
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
    description="Upload user avatar image (max 5MB, jpg/png/webp)",
)
async def upload_avatar(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    """Upload user avatar"""
    
    avatar_url = await upload_user_avatar(session, current_user, file)
    return {"avatar_url": avatar_url, "message": "Avatar uploaded successfully"}


@router.delete(
    "/me/avatar",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete avatar",
    description="Remove user avatar image",
)
async def delete_avatar(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Delete user avatar"""
    
    await delete_user_avatar(session, current_user)
    return None


@router.post(
    "/me/cover-photo",
    status_code=status.HTTP_200_OK,
    summary="Upload cover photo",
    description="Upload user cover photo (max 5MB, jpg/png/webp)",
)
async def upload_cover(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    """Upload user cover photo"""
    cover_url = await upload_cover_photo(session, current_user, file)
    return {"cover_photo_url": cover_url, "message": "Cover photo uploaded successfully"}


@router.delete(
    "/me/cover-photo",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete cover photo",
    description="Remove user cover photo",
)
async def delete_cover(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Delete user cover photo"""
    await delete_cover_photo(session, current_user)
    return None


@router.get(
    "/me/preferences",
    response_model=UserPreferencesResponse,
    summary="Get user preferences",
    description="Get current user's preferences (theme, language, timezone, etc.)",
)
async def get_preferences(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Get user preferences"""
    return await get_user_preferences(session, current_user.id)


@router.put(
    "/me/preferences",
    response_model=UserPreferencesResponse,
    summary="Update user preferences",
    description="Update user preferences (theme, language, timezone, currency, privacy)",
)
async def update_preferences(
    data: UserPreferencesUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Update user preferences"""
    return await update_user_preferences(session, current_user.id, data)


@router.get(
    "/me/stats",
    response_model=UserStatsResponse,
    summary="Get user stats",
    description="Get aggregated user statistics (events organized, attended, reviews)",
)
async def get_stats(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Get user statistics"""
    return await get_user_stats(session, current_user.id)


@router.get(
    "/me/activity",
    response_model=UserActivityResponse,
    summary="Get user activity",
    description="Get recent activity timeline (registrations, event creations, reviews)",
)
async def get_activity(
    current_user: CurrentUser,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Get user activity timeline"""
    return await get_user_activity(session, current_user.id, limit, offset)
