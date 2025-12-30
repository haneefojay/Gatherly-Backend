"""User API router"""

from fastapi import APIRouter

from app.users.routes import router as users_router

router = APIRouter()
router.include_router(users_router)
