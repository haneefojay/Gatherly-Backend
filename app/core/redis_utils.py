import redis.asyncio as redis
from app.core.settings import get_settings

settings = get_settings()

class RedisClient:
    _client: redis.Redis | None = None

    @classmethod
    async def get_client(cls) -> redis.Redis:
        if cls._client is None:
            cls._client = redis.from_url(
                settings.REDIS_BROKER_URL, 
                encoding="utf-8", 
                decode_responses=True
            )
        return cls._client

    @classmethod
    async def close(cls):
        if cls._client:
            await cls._client.close()
            cls._client = None
