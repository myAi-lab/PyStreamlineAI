import uuid
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate_profile import CandidateProfile


class CandidateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(self, user_id: UUID) -> CandidateProfile | None:
        stmt: Select[tuple[CandidateProfile]] = select(CandidateProfile).where(
            CandidateProfile.user_id == user_id
        )
        return await self.session.scalar(stmt)

    async def create_for_user(self, user_id: UUID) -> CandidateProfile:
        profile = CandidateProfile(
            id=uuid.uuid4(),
            user_id=user_id,
            headline=None,
            years_experience=None,
            target_roles=[],
            location=None,
            role_profile={},
        )
        self.session.add(profile)
        await self.session.flush()
        return profile
