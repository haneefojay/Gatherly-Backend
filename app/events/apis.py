"""Event API router"""

from app.events.routes import router, categories_router, tags_router, media_router

__all__ = ["router", "categories_router", "tags_router", "media_router"]

