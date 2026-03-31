from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, refresh_token: RefreshToken) -> RefreshToken:
        self.session.add(refresh_token)
        await self.session.flush()
        return refresh_token

    async def get_by_jti(self, token_jti: str) -> RefreshToken | None:
        stmt: Select[tuple[RefreshToken]] = select(RefreshToken).where(
            RefreshToken.token_jti == token_jti
        )
        return await self.session.scalar(stmt)

    async def revoke(self, token: RefreshToken) -> RefreshToken:
        token.is_revoked = True
        await self.session.flush()
        return token

    async def revoke_expired_tokens(self, now: datetime) -> int:
        stmt: Select[tuple[RefreshToken]] = select(RefreshToken).where(RefreshToken.expires_at < now)
        tokens = list(await self.session.scalars(stmt))
        for token in tokens:
            token.is_revoked = True
        await self.session.flush()
        return len(tokens)

