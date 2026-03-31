from collections.abc import AsyncGenerator

from redis.asyncio import Redis
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)

redis_client: Redis | None = None


async def init_redis() -> None:
    global redis_client
    settings = get_settings()
    if not settings.redis_enabled:
        redis_client = None
        return

    redis_client = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        await redis_client.ping()
        logger.info("redis_connected")
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.warning("redis_connection_failed", error=str(exc))
        redis_client = None


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None


async def get_redis() -> AsyncGenerator[Redis | None, None]:
    yield redis_client

