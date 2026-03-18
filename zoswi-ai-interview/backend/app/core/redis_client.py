from __future__ import annotations

from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()


@lru_cache(maxsize=1)
def get_redis_client() -> Redis | None:
    redis_url = str(settings.redis_url or "").strip()
    if not redis_url:
        return None
    return Redis.from_url(redis_url, decode_responses=True)
