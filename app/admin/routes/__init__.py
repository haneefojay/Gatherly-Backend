"""Admin routes package"""

from fastapi import APIRouter

from app.admin.routes.base import router as base_router
from app.admin.routes.admin_users import router as admin_users_router

router = APIRouter()

router.include_router(base_router)
router.include_router(admin_users_router, prefix="/users", tags=["Admin Users"])
