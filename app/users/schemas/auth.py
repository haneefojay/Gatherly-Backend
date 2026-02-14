"""Authentication schemas"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request schema"""

    email: EmailStr
    password: str
    totp_code: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
            }
        }


UserLogin = LoginRequest


class TokenPayload(BaseModel):
    """Payload and subject structure for JWT tokens"""

    sub: str | None = None
    type: str | None = None
    exp: int | None = None
    iat: int | None = None


class TokenResponse(BaseModel):
    """Token response schema"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""

    refresh_token: str

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }


class AccessTokenResponse(BaseModel):
    """Access token response schema"""

    access_token: str
    token_type: str = "bearer"

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }


class VerifyEmailRequest(BaseModel):
    """Email verification request schema"""

    token: str = Field(..., description="Verification token from email")

    class Config:
        json_schema_extra = {"example": {"token": "abc123def456"}}


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema"""

    email: EmailStr

    class Config:
        json_schema_extra = {"example": {"email": "user@example.com"}}


class ResetPasswordRequest(BaseModel):
    """Reset password request schema"""

    token: str = Field(..., description="Reset token from email")
    new_password: str = Field(..., min_length=8, description="New password")

    class Config:
        json_schema_extra = {
            "example": {"token": "abc123def456", "new_password": "NewSecurePass123!"}
        }


class ResendVerificationEmailRequest(BaseModel):
    """Resend verification email request schema"""

    email: EmailStr

    class Config:
        json_schema_extra = {"example": {"email": "user@example.com"}}
