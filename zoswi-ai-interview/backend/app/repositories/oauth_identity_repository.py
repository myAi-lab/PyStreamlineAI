from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.oauth_identity import OAuthIdentity


class OAuthIdentityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_provider_identity(
        self,
        *,
        provider: str,
        provider_user_id: str,
    ) -> OAuthIdentity | None:
        stmt: Select[tuple[OAuthIdentity]] = select(OAuthIdentity).where(
            OAuthIdentity.provider == provider,
            OAuthIdentity.provider_user_id == provider_user_id,
        )
        return await self.session.scalar(stmt)

    async def create(self, identity: OAuthIdentity) -> OAuthIdentity:
        self.session.add(identity)
        await self.session.flush()
        return identity

