import redis.asyncio as redis
from app.core.settings import get_settings

settings = get_settings()

async def init_redis_cache():
    """Initialize Redis connection pool for caching"""
    pool = redis.ConnectionPool.from_url(
        settings.REDIS_BROKER_URL,
        encoding="utf8",
        decode_responses=True
    )
    redis_client = redis.Redis(connection_pool=pool)
    await redis_client.ping()
    return redis_client
