"""User routes package"""

from fastapi import APIRouter

from app.users.routes.auth import router as auth_router
from app.users.routes.users import router as users_router
from app.users.routes.dashboard import router as dashboard_router
from app.users.routes.profile import router as profile_router
from app.users.routes.twofa import router as twofa_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(profile_router, prefix="/profile", tags=["Profile"])
router.include_router(twofa_router, prefix="/2fa", tags=["Two-Factor Authentication"])
router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
