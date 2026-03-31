from uuid import UUID

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis


class ResumeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, resume: Resume) -> Resume:
        self.session.add(resume)
        await self.session.flush()
        return resume

    async def list_for_user(self, user_id: UUID) -> list[Resume]:
        stmt: Select[tuple[Resume]] = (
            select(Resume).where(Resume.user_id == user_id).order_by(desc(Resume.created_at))
        )
        result = await self.session.scalars(stmt)
        return list(result)

    async def get_for_user(self, *, user_id: UUID, resume_id: UUID) -> Resume | None:
        stmt: Select[tuple[Resume]] = select(Resume).where(
            Resume.user_id == user_id,
            Resume.id == resume_id,
        )
        return await self.session.scalar(stmt)

    async def get_by_id(self, resume_id: UUID) -> Resume | None:
        stmt: Select[tuple[Resume]] = select(Resume).where(Resume.id == resume_id)
        return await self.session.scalar(stmt)

    async def upsert_analysis(self, analysis: ResumeAnalysis) -> ResumeAnalysis:
        existing_stmt: Select[tuple[ResumeAnalysis]] = select(ResumeAnalysis).where(
            ResumeAnalysis.resume_id == analysis.resume_id
        )
        existing = await self.session.scalar(existing_stmt)
        if existing is None:
            self.session.add(analysis)
            await self.session.flush()
            return analysis

        existing.extracted_skills = analysis.extracted_skills
        existing.strengths = analysis.strengths
        existing.weaknesses = analysis.weaknesses
        existing.suggestions = analysis.suggestions
        existing.summary = analysis.summary
        existing.model_name = analysis.model_name
        existing.analysis_version = analysis.analysis_version
        await self.session.flush()
        return existing

    async def get_analysis(self, resume_id: UUID) -> ResumeAnalysis | None:
        stmt: Select[tuple[ResumeAnalysis]] = select(ResumeAnalysis).where(
            ResumeAnalysis.resume_id == resume_id
        )
        return await self.session.scalar(stmt)

    async def get_latest_analysis_for_user(self, user_id: UUID) -> ResumeAnalysis | None:
        stmt: Select[tuple[ResumeAnalysis]] = (
            select(ResumeAnalysis)
            .join(Resume, Resume.id == ResumeAnalysis.resume_id)
            .where(Resume.user_id == user_id)
            .order_by(desc(ResumeAnalysis.created_at))
        )
        return await self.session.scalar(stmt)

