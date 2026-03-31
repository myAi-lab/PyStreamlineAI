from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import PlatformJob


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, job: PlatformJob) -> PlatformJob:
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_by_id(self, job_id: UUID) -> PlatformJob | None:
        stmt: Select[tuple[PlatformJob]] = select(PlatformJob).where(PlatformJob.id == job_id)
        return await self.session.scalar(stmt)

