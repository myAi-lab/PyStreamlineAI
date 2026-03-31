from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import JobStatus, JobType
from app.models.job import PlatformJob
from app.repositories.job_repository import JobRepository


class JobService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = JobRepository(session)

    async def create_job(
        self,
        *,
        job_type: JobType,
        payload: dict,
        user_id: UUID | None = None,
    ) -> PlatformJob:
        job = PlatformJob(
            user_id=user_id,
            job_type=job_type,
            status=JobStatus.QUEUED,
            payload=payload,
        )
        await self.repo.create(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def mark_running(self, job: PlatformJob) -> PlatformJob:
        job.status = JobStatus.RUNNING
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def mark_succeeded(self, job: PlatformJob, result: dict) -> PlatformJob:
        job.status = JobStatus.SUCCEEDED
        job.result = result
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def mark_failed(self, job: PlatformJob, error: str) -> PlatformJob:
        job.status = JobStatus.FAILED
        job.error = error[:1000]
        await self.session.commit()
        await self.session.refresh(job)
        return job

