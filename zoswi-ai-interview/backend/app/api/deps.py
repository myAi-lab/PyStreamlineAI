from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Request
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.correlation import get_request_id
from app.core.exceptions import AuthenticationError, AuthorizationError, RateLimitError
from app.core.rate_limit import RateLimiter
from app.core.redis import get_redis
from app.core.security import decode_token
from app.db.session import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
RedisDep = Annotated[Redis | None, Depends(get_redis)]


def get_request_id_value() -> str | None:
    return get_request_id()


async def enforce_rate_limit(
    request: Request,
    redis_client: RedisDep,
    x_forwarded_for: str | None = Header(default=None),
) -> None:
    client_ip = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else request.client.host
    limiter = RateLimiter(redis_client)
    key = f"{client_ip}:{request.url.path}"
    allowed = await limiter.allow(key=key)
    if not allowed:
        raise RateLimitError("Rate limit exceeded")


async def get_current_user(
    session: DBSessionDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    claims = decode_token(token)
    if claims.type != "access":
        raise AuthenticationError("Access token required")
    try:
        user_id = UUID(claims.sub)
    except ValueError as exc:
        raise AuthenticationError("Invalid token subject") from exc
    user = await UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("User not active")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole) -> Callable[[CurrentUserDep], User]:
    async def _role_guard(user: CurrentUserDep) -> User:
        if user.role not in set(roles):
            raise AuthorizationError("Insufficient role permissions")
        return user

    return _role_guard
