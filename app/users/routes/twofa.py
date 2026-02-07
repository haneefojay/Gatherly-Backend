"""Two-factor authentication routes"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_session
from app.common.permissions import CurrentUser
from app.users.schemas import (
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    TwoFactorDisableRequest,
    BackupCodesResponse,
)
from app.users.services.twofa import (
    setup_two_factor,
    verify_and_enable_two_factor,
    disable_two_factor,
    regenerate_backup_codes,
)

router = APIRouter()


@router.post(
    "/setup",
    response_model=TwoFactorSetupResponse,
    summary="Setup 2FA",
    description="Initialize 2FA setup - returns secret, QR code URI, and backup codes",
)
async def setup_2fa(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Setup two-factor authentication"""
    return await setup_two_factor(session, current_user)


@router.post(
    "/verify",
    status_code=status.HTTP_200_OK,
    summary="Verify and enable 2FA",
    description="Verify TOTP code from authenticator app to enable 2FA",
)
async def verify_2fa(
    data: TwoFactorVerifyRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Verify 2FA code and enable"""
    await verify_and_enable_two_factor(session, current_user, data.code)
    return {"message": "Two-factor authentication enabled successfully"}


@router.post(
    "/disable",
    status_code=status.HTTP_200_OK,
    summary="Disable 2FA",
    description="Disable two-factor authentication (requires password and optional 2FA code)",
)
async def disable_2fa(
    data: TwoFactorDisableRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Disable two-factor authentication"""
    await disable_two_factor(session, current_user, data.password, data.code)
    return {"message": "Two-factor authentication disabled successfully"}


@router.post(
    "/regenerate-backup-codes",
    response_model=BackupCodesResponse,
    summary="Regenerate backup codes",
    description="Generate new backup codes (invalidates old ones)",
)
async def regenerate_codes(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Regenerate backup codes"""
    return await regenerate_backup_codes(session, current_user)
