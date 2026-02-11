"""Authentication routes"""

from fastapi import APIRouter, Depends, status, Request
from sqlalchemy import select
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
    VerifyEmailRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.users.services.users import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    revoke_refresh_token,
    verify_refresh_token,
    generate_email_verification_token,
    reset_password_with_token,
    generate_password_reset_token,
    verify_email_token,
)
from app.external.email import email_service

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
    
    verification_token = await generate_email_verification_token(session, user)
    email_service.send_verification_email(user.email, verification_token, user.full_name)
    
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    description="Authenticate user and receive access and refresh tokens",
)
async def login(
    credentials: LoginRequest, 
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Login and receive JWT tokens"""
    from datetime import datetime, timedelta
    from app.users.services.twofa import check_user_2fa_enabled, verify_two_factor_code
    from app.users.models import UserSession, RefreshToken
    from app.core.settings import get_settings
    import hashlib
    
    settings = get_settings()
    
    user = await authenticate_user(session, credentials.email, credentials.password)

    if not user:
        raise Unauthorized("Invalid email or password")
    
    if await check_user_2fa_enabled(session, user.id):
        if not credentials.totp_code:
            raise Unauthorized("Two-factor authentication code required")
        
        if not await verify_two_factor_code(session, user, credentials.totp_code):
            raise Unauthorized("Invalid two-factor authentication code")

    # Update last login timestamp
    user.last_login_at = datetime.utcnow()

    access_token = await create_access_token(user)
    refresh_token = await create_refresh_token(session, user)
    
    # Get refresh token ID from database
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    refresh_token_record = result.scalar_one()
    
    # Create user session
    user_agent = request.headers.get("user-agent", "Unknown")
    client_ip = request.client.host if request.client else None
    
    user_session = UserSession(
        user_id=user.id,
        refresh_token_id=refresh_token_record.id,
        session_token=token_hash[:100],  # Use part of token hash as session token
        device_info=user_agent,
        ip_address=client_ip,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    session.add(user_session)
    
    await session.commit()

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


@router.post(
    "/verify-email",
    response_model=TokenResponse,
    summary="Verify email address",
    description="Verify email using token from verification email and auto-login",
)
async def verify_email(
    data: VerifyEmailRequest, session: AsyncSession = Depends(get_session)
):
    """Verify email and auto-login"""
    
    user = await verify_email_token(session, data.token)
    
    access_token = await create_access_token(user)
    refresh_token = await create_refresh_token(session, user)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Send password reset email if account exists",
)
async def forgot_password(
    data: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)
):
    """Request password reset email"""
    
    result = await generate_password_reset_token(session, data.email)
    
    if result:
        user, token = result
        email_service.send_password_reset_email(user.email, token, user.full_name)
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Reset password using token from reset email",
)
async def reset_password(
    data: ResetPasswordRequest, session: AsyncSession = Depends(get_session)
):
    """Reset password with token"""
    
    await reset_password_with_token(session, data.token, data.new_password)
    
    return {"message": "Password reset successfully"}
