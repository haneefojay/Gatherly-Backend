"""User schemas package"""

from app.users.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshTokenRequest,
    TokenPayload,
    TokenResponse,
    UserLogin,
    VerifyEmailRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ResendVerificationEmailRequest,
)
from app.users.schemas.base import UserBase
from app.users.schemas.create import UserCreate
from app.users.schemas.edit import UserRoleUpdate, UserUpdate
from app.users.schemas.response import UserResponse
from app.users.schemas.profile import (
    ProfileUpdate,
    ChangePasswordRequest,
    SessionResponse,
    UserPreferences,
    UserPreferencesUpdate2,
)
from app.users.schemas.twofa import (
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    TwoFactorDisableRequest,
    BackupCodesResponse,
)
from app.users.schemas.public_profile import (
    PublicProfileResponse,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserStatsResponse,
    UserActivityItem,
    UserActivityResponse,
)

__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "LoginRequest",
    "TokenResponse",
    "TokenPayload",
    "UserRoleUpdate",
    "RefreshTokenRequest",
    "AccessTokenResponse",
    "VerifyEmailRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "ResendVerificationEmailRequest",
    "ProfileUpdate",
    "ChangePasswordRequest",
    "SessionResponse",
    "TwoFactorSetupResponse",
    "TwoFactorVerifyRequest",
    "TwoFactorDisableRequest",
    "BackupCodesResponse",
    "PublicProfileResponse",
    "UserPreferencesResponse",
    "UserPreferencesUpdate",
    "UserStatsResponse",
    "UserActivityItem",
    "UserActivityResponse",
    "UserPreferences",
    "UserPreferencesUpdate2",
]
