"""Two-factor authentication schemas"""

from pydantic import BaseModel, Field


class TwoFactorSetupResponse(BaseModel):
    """2FA setup response with QR code data"""

    secret: str = Field(..., description="TOTP secret key")
    qr_code_uri: str = Field(..., description="otpauth:// URI for QR code")
    backup_codes: list[str] = Field(..., description="One-time backup codes")

    class Config:
        json_schema_extra = {
            "example": {
                "secret": "JBSWY3DPEHPK3PXP",
                "qr_code_uri": "otpauth://totp/Gatherly:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Gatherly",
                "backup_codes": ["12345678", "87654321", "11223344"],
            }
        }


class TwoFactorVerifyRequest(BaseModel):
    """Verify 2FA code to enable it"""

    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")

    class Config:
        json_schema_extra = {"example": {"code": "123456"}}


class TwoFactorDisableRequest(BaseModel):
    """Disable 2FA request"""

    password: str = Field(..., description="User password for verification")
    code: str | None = Field(None, min_length=6, max_length=6, description="6-digit TOTP code or backup code")

    class Config:
        json_schema_extra = {
            "example": {"password": "MyPassword123!", "code": "123456"}
        }


class BackupCodesResponse(BaseModel):
    """Backup codes response"""

    backup_codes: list[str] = Field(..., description="New backup codes")

    class Config:
        json_schema_extra = {
            "example": {"backup_codes": ["12345678", "87654321", "11223344"]}
        }
