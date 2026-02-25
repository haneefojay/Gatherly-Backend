"""Admin user management schemas"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminUserListItem(BaseModel):
    """Single user in admin list view"""

    id: UUID
    email: str
    username: str | None = None
    full_name: str
    role: str
    status: str
    email_verified: bool
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    """Paginated user list response"""

    users: list[AdminUserListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminUserDetailResponse(BaseModel):
    """Complete user detail for admin view"""

    id: UUID
    email: str
    username: str | None = None
    full_name: str
    role: str
    status: str
    email_verified: bool
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    bio: str | None = None
    phone: str | None = None
    location: str | None = None
    avatar_url: str | None = None
    cover_photo_url: str | None = None
    social_links: dict | None = None

    has_2fa: bool = False
    login_history: list[dict] = []
    active_sessions: list[dict] = []
    created_events: list[dict] = []
    attended_events: list[dict] = []
    reviews_given: list[dict] = []
    reviews_received: list[dict] = []
    admin_notes: list[dict] = []


class AdminUserUpdateRequest(BaseModel):
    """Admin update user request"""

    full_name: str | None = None
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=100)
    role: str | None = Field(None, pattern="^(user|organizer|admin)$")
    email_verified: bool | None = None


class SuspendUserRequest(BaseModel):
    """Suspend user request"""

    reason: str = Field(..., min_length=5, max_length=500)
    duration_days: int | None = Field(None, ge=1, le=365, description="Null = permanent")


class BanUserRequest(BaseModel):
    """Ban user request"""

    reason: str = Field(..., min_length=5, max_length=500)


class AdminNoteCreate(BaseModel):
    """Create admin note"""

    content: str = Field(..., min_length=1, max_length=2000)


class AdminNoteResponse(BaseModel):
    """Admin note response"""

    id: UUID
    admin_email: str | None = None
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminUserStatsResponse(BaseModel):
    """User analytics dashboard"""

    total_users: int = 0
    active_users: int = 0
    new_today: int = 0
    new_this_week: int = 0
    new_this_month: int = 0
    by_role: dict = {}
    by_status: dict = {}
    email_verified_rate: float = 0.0
    twofa_adoption_rate: float = 0.0
    dau: int = 0
    wau: int = 0
    mau: int = 0


class UserGrowthDataPoint(BaseModel):
    """Single growth data point"""

    date: str
    count: int
    cumulative: int


class UserGrowthResponse(BaseModel):
    """User growth over time"""

    data_points: list[UserGrowthDataPoint]
    period: str


class BulkActionRequest(BaseModel):
    """Bulk action request"""

    action: str = Field(..., pattern="^(suspend|unsuspend|verify|export|email|notify)$")
    user_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    reason: str | None = None
    duration_days: int | None = None


class BulkActionResponse(BaseModel):
    """Bulk action result"""

    success_count: int = 0
    failed_count: int = 0
    errors: list[str] = []
