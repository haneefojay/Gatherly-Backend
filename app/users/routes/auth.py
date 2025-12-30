"""Authentication routes"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_session
from app.common.exceptions import Unauthorized
from app.common.permissions import CurrentUser
from app.users.schemas import (
    AccessTokenResponse,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.users.services import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    revoke_refresh_token,
    verify_refresh_token,
)

router = APIRouter()


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password",
)
async def signup(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    """Register a new user"""
    user = await create_user(session, user_data)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    description="Authenticate user and receive access and refresh tokens",
)
async def login(
    credentials: LoginRequest, session: AsyncSession = Depends(get_session)
):
    """Login and receive JWT tokens"""
    user = await authenticate_user(session, credentials.email, credentials.password)

    if not user:
        raise Unauthorized("Invalid email or password")

    # Generate tokens
    access_token = await create_access_token(user)
    refresh_token = await create_refresh_token(session, user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Refresh access token",
    description="Exchange refresh token for a new access token",
)
async def refresh_access_token(
    token_data: RefreshTokenRequest, session: AsyncSession = Depends(get_session)
):
    """Refresh access token using refresh token"""
    user = await verify_refresh_token(session, token_data.refresh_token)

    # Generate new access token
    access_token = await create_access_token(user)

    return AccessTokenResponse(access_token=access_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="Revoke refresh token to logout user",
)
async def logout(
    token_data: RefreshTokenRequest, session: AsyncSession = Depends(get_session)
):
    """Logout by revoking refresh token"""
    await revoke_refresh_token(session, token_data.refresh_token)
    return None


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieve the authenticated user's profile information",
)
async def get_me(current_user: CurrentUser):
    """Get current user profile"""
    return current_user
