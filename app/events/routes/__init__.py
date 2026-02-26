"""Event routes package"""

from app.events.routes.base import router
from app.events.routes.categories import router as categories_router
from app.events.routes.tags import router as tags_router
from app.events.routes.media import router as media_router

__all__ = ["router", "categories_router", "tags_router", "media_router"]

