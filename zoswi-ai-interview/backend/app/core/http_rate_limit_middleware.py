from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.rate_limit import limiter

settings = get_settings()


class HttpRateLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        ip_address = request.client.host if request.client else "unknown"
        user_id = str(request.headers.get("x-user-id", "")).strip()
        identity = user_id or ip_address
        minute_bucket = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
        key = f"ratelimit:http:{identity}:{minute_bucket}"
        allowed, remaining = await limiter.hit(
            key=key,
            limit=max(1, int(settings.api_requests_per_minute)),
            window_seconds=60,
        )
        if not allowed:
            response = JSONResponse(status_code=429, content={"error": "API rate limit reached."})
            await response(scope, receive, send)
            return

        async def send_wrapper(message):
            if message.get("type") == "http.response.start":
                headers = message.setdefault("headers", [])
                headers.append((b"x-ratelimit-remaining", str(remaining).encode("utf-8")))
            await send(message)

        await self.app(scope, receive, send_wrapper)
