from datetime import UTC, datetime
from hashlib import sha256

from redis.asyncio import Redis

from app.core.config import get_settings


class RateLimiter:
    def __init__(self, redis_client: Redis | None) -> None:
        self.redis = redis_client
        self.settings = get_settings()

    async def allow(self, *, key: str) -> bool:
        if self.redis is None:
            return True

        current_minute = datetime.now(UTC).strftime("%Y%m%d%H%M")
        digest = sha256(key.encode("utf-8")).hexdigest()
        redis_key = f"ratelimit:{digest}:{current_minute}"

        count = await self.redis.incr(redis_key)
        if count == 1:
            await self.redis.expire(redis_key, 70)
        return count <= self.settings.rate_limit_requests_per_minute

