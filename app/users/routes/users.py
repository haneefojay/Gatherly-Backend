"""User management routes"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.dependencies import get_session
from app.common.permissions import AdminUser, CurrentUser, OrganizerOrAdminUser
from app.users.models import User, UserRole
from app.users.schemas import UserResponse, UserRoleUpdate, UserUpdate
from app.users.services.users import update_user_role

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieve the authenticated user's profile information",
)
async def get_current_user_profile(current_user: CurrentUser):
    """Get current user profile"""
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update the authenticated user's profile information",
)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Update current user profile"""

    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name
    if user_data.email is not None:
        current_user.email = user_data.email

    await session.commit()
    await session.refresh(current_user)

    return current_user


@router.put(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Update user role (Admin only)",
    description="Update a user's role. Only accessible by administrators.",
)
async def update_user_role_endpoint(
    user_id: uuid.UUID,
    role_data: UserRoleUpdate,
    admin_user: AdminUser,
    session: AsyncSession = Depends(get_session),
):
    """Update user role (Admin only)"""
    user = await update_user_role(session, user_id, role_data.role)
    return user


@router.get(
    "",
    response_model=list[UserResponse],
    summary="List users",
    description="List users with optional filtering. Organizer/Admin only.",
)
async def list_users(
    role: UserRole | None = None,
    search: str | None = None,
    current_user: OrganizerOrAdminUser = None, 
    session: AsyncSession = Depends(get_session),
):
    """List users"""
    query = select(User).options(selectinload(User.profile))
    
    if role:
        query = query.where(User.role == role)
        
    if search:
        query = query.where(
            (User.email.ilike(f"%{search}%")) | 
            (User.full_name.ilike(f"%{search}%"))
        )
        
    # Limit to 20 results to avoid heavy load, as this is for autocomplete
    query = query.limit(20)
    
    result = await session.execute(query)
    users = result.scalars().all()
    return users
