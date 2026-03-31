from datetime import UTC, datetime, timedelta
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


class TokenClaims(BaseModel):
    sub: str
    type: str
    role: str | None = None
    jti: str | None = None
    exp: int
    iat: int


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def _create_token(
    *,
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    role: str | None = None,
    jti: str | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, str | int] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    if role is not None:
        payload["role"] = role
    if jti is not None:
        payload["jti"] = jti
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(*, subject: str, role: str) -> str:
    settings = get_settings()
    return _create_token(
        subject=subject,
        token_type="access",
        role=role,
        expires_delta=timedelta(minutes=settings.access_token_exp_minutes),
    )


def create_refresh_token(*, subject: str, jti: str | None = None) -> tuple[str, str]:
    settings = get_settings()
    token_jti = jti or str(uuid.uuid4())
    token = _create_token(
        subject=subject,
        token_type="refresh",
        jti=token_jti,
        expires_delta=timedelta(days=settings.refresh_token_exp_days),
    )
    return token, token_jti


def create_oauth_state_token(*, provider: str) -> str:
    settings = get_settings()
    return _create_token(
        subject=provider,
        token_type="oauth_state",
        expires_delta=timedelta(minutes=settings.oauth_state_exp_minutes),
        jti=str(uuid.uuid4()),
    )


def create_oauth_bridge_token(*, subject: str) -> str:
    settings = get_settings()
    return _create_token(
        subject=subject,
        token_type="oauth_bridge",
        expires_delta=timedelta(minutes=settings.oauth_bridge_exp_minutes),
        jti=str(uuid.uuid4()),
    )


def decode_token(token: str) -> TokenClaims:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return TokenClaims.model_validate(payload)
    except JWTError as exc:
        raise AuthenticationError("Invalid token") from exc
