from typing import Literal

import redis.asyncio as redis

from app.common.types import PaginationParamsType
from app.core.database import AsyncSessionLocal
from app.core.settings import get_settings

settings = get_settings()


async def get_session():
    """
    Start a db session
    """
    async with AsyncSessionLocal() as session:
        yield session


def pagination_params(
    q: str | None = None,
    page: int = 1,
    size: int = 10,
    sort_by: str | None = "date",
    order_by: Literal["asc", "desc"] = "desc",
):
    """
    Helper Dependency for pagination
    """
    return PaginationParamsType(q=q, page=page, size=size, sort_by=sort_by, order_by=order_by)


async def get_redis_client():
    """
    Helper dependency for redis. Returns a singleton client.
    """
    from app.core.redis_utils import RedisClient
    return await RedisClient.get_client()
