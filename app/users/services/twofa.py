"""Two-factor authentication service functions"""

import hashlib
import secrets
import uuid
from typing import Optional

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import (
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.users.models import User, TwoFactorAuth
from app.users.schemas.twofa import (
    TwoFactorSetupResponse,
    BackupCodesResponse,
)

ph = PasswordHasher()


def generate_backup_codes(count: int = 8) -> list[str]:
    """Generate backup codes for 2FA recovery
    
    Args:
        count: Number of backup codes to generate
        
    Returns:
        List of backup codes
    """
    return [secrets.token_hex(4).upper() for _ in range(count)]


async def setup_two_factor(
    session: AsyncSession, user: User
) -> TwoFactorSetupResponse:
    """Initialize 2FA setup for user
    
    Args:
        session: Database session
        user: Current user
        
    Returns:
        2FA setup response with secret and QR code URI
        
    Raises:
        ValidationException: If 2FA already enabled
    """
    result = await session.execute(
        select(TwoFactorAuth).where(
            TwoFactorAuth.user_id == user.id,
            TwoFactorAuth.enabled == True
        )
    )
    existing_2fa = result.scalar_one_or_none()
    
    if existing_2fa:
        raise ValidationException("Two-factor authentication is already enabled")
    
    secret = pyotp.random_base32()
    
    totp = pyotp.TOTP(secret)
    qr_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name="Gatherly"
    )
    
    backup_codes = generate_backup_codes()
    backup_codes_hashed = [
        hashlib.sha256(code.encode()).hexdigest()
        for code in backup_codes
    ]
    
    result = await session.execute(
        select(TwoFactorAuth).where(TwoFactorAuth.user_id == user.id)
    )
    twofa = result.scalar_one_or_none()
    
    if twofa:
        twofa.secret_key = secret
        twofa.backup_codes = backup_codes_hashed
        twofa.enabled = False
    else:
        twofa = TwoFactorAuth(
            user_id=user.id,
            secret_key=secret,
            backup_codes=backup_codes_hashed,
            enabled=False,
        )
        session.add(twofa)
    
    await session.commit()
    
    return TwoFactorSetupResponse(
        secret=secret,
        qr_code_uri=qr_uri,
        backup_codes=backup_codes,
    )


async def verify_and_enable_two_factor(
    session: AsyncSession, user: User, code: str
) -> bool:
    """Verify TOTP code and enable 2FA
    
    Args:
        session: Database session
        user: Current user
        code: 6-digit TOTP code
        
    Returns:
        True if verified and enabled
        
    Raises:
        NotFoundException: If 2FA not set up
        UnauthorizedException: If code is invalid
    """
    result = await session.execute(
        select(TwoFactorAuth).where(TwoFactorAuth.user_id == user.id)
    )
    twofa = result.scalar_one_or_none()
    
    if not twofa or not twofa.secret_key:
        raise NotFoundException("Two-factor authentication not set up")
    
    totp = pyotp.TOTP(twofa.secret_key)
    
    if not totp.verify(code, valid_window=1):
        raise UnauthorizedException("Invalid verification code")
    
    twofa.enabled = True
    await session.commit()
    
    return True


async def verify_two_factor_code(
    session: AsyncSession, user: User, code: str
) -> bool:
    """Verify 2FA code (TOTP or backup code)
    
    Args:
        session: Database session
        user: Current user
        code: TOTP code or backup code
        
    Returns:
        True if code is valid
    """
    result = await session.execute(
        select(TwoFactorAuth).where(
            TwoFactorAuth.user_id == user.id,
            TwoFactorAuth.enabled == True
        )
    )
    twofa = result.scalar_one_or_none()
    
    if not twofa:
        return False
    
    totp = pyotp.TOTP(twofa.secret_key)
    if totp.verify(code, valid_window=1):
        return True
    
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    if code_hash in twofa.backup_codes:
        twofa.backup_codes.remove(code_hash)
        await session.commit()
        return True
    
    return False


async def disable_two_factor(
    session: AsyncSession, user: User, password: str, code: Optional[str] = None
) -> None:
    """Disable 2FA for user
    
    Args:
        session: Database session
        user: Current user
        password: User password for verification
        code: Optional 2FA code
        
    Raises:
        UnauthorizedException: If password or code is invalid
        NotFoundException: If 2FA not enabled
    """
    try:
        ph.verify(user.hashed_password, password)
    except VerifyMismatchError:
        raise UnauthorizedException("Invalid password")
    
    result = await session.execute(
        select(TwoFactorAuth).where(
            TwoFactorAuth.user_id == user.id,
            TwoFactorAuth.enabled == True
        )
    )
    twofa = result.scalar_one_or_none()
    
    if not twofa:
        raise NotFoundException("Two-factor authentication not enabled")
    
    if code:
        if not await verify_two_factor_code(session, user, code):
            raise UnauthorizedException("Invalid 2FA code")
    
    twofa.enabled = False
    twofa.secret_key = None
    twofa.backup_codes = []
    await session.commit()


async def regenerate_backup_codes(
    session: AsyncSession, user: User
) -> BackupCodesResponse:
    """Regenerate backup codes for user
    
    Args:
        session: Database session
        user: Current user
        
    Returns:
        New backup codes
        
    Raises:
        NotFoundException: If 2FA not enabled
    """
    result = await session.execute(
        select(TwoFactorAuth).where(
            TwoFactorAuth.user_id == user.id,
            TwoFactorAuth.enabled == True
        )
    )
    twofa = result.scalar_one_or_none()
    
    if not twofa:
        raise NotFoundException("Two-factor authentication not enabled")
    
    backup_codes = generate_backup_codes()
    backup_codes_hashed = [
        hashlib.sha256(code.encode()).hexdigest()
        for code in backup_codes
    ]
    
    twofa.backup_codes = backup_codes_hashed
    await session.commit()
    
    return BackupCodesResponse(backup_codes=backup_codes)


async def check_user_2fa_enabled(
    session: AsyncSession, user_id: uuid.UUID
) -> bool:
    """Check if user has 2FA enabled
    
    Args:
        session: Database session
        user_id: User ID
        
    Returns:
        True if 2FA is enabled
    """
    result = await session.execute(
        select(TwoFactorAuth).where(
            TwoFactorAuth.user_id == user_id,
            TwoFactorAuth.enabled == True
        )
    )
    twofa = result.scalar_one_or_none()
    return twofa is not None
