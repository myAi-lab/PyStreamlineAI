from uuid import UUID

from sqlalchemy import Select, and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import InterviewSession, InterviewSummary, InterviewTurn


class InterviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_session(self, interview_session: InterviewSession) -> InterviewSession:
        self.session.add(interview_session)
        await self.session.flush()
        return interview_session

    async def list_sessions_for_user(self, user_id: UUID) -> list[InterviewSession]:
        stmt: Select[tuple[InterviewSession]] = (
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id)
            .order_by(desc(InterviewSession.created_at))
        )
        result = await self.session.scalars(stmt)
        return list(result)

    async def get_session_for_user(self, *, user_id: UUID, session_id: UUID) -> InterviewSession | None:
        stmt: Select[tuple[InterviewSession]] = select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        )
        return await self.session.scalar(stmt)

    async def get_session(self, session_id: UUID) -> InterviewSession | None:
        stmt: Select[tuple[InterviewSession]] = select(InterviewSession).where(InterviewSession.id == session_id)
        return await self.session.scalar(stmt)

    async def count_turns(self, session_id: UUID) -> int:
        stmt = select(func.count(InterviewTurn.id)).where(InterviewTurn.session_id == session_id)
        value = await self.session.scalar(stmt)
        return int(value or 0)

    async def list_turns(self, session_id: UUID) -> list[InterviewTurn]:
        stmt: Select[tuple[InterviewTurn]] = (
            select(InterviewTurn)
            .where(InterviewTurn.session_id == session_id)
            .order_by(InterviewTurn.turn_index.asc())
        )
        result = await self.session.scalars(stmt)
        return list(result)

    async def get_last_turn(self, session_id: UUID) -> InterviewTurn | None:
        stmt: Select[tuple[InterviewTurn]] = (
            select(InterviewTurn)
            .where(InterviewTurn.session_id == session_id)
            .order_by(InterviewTurn.turn_index.desc())
        )
        return await self.session.scalar(stmt)

    async def get_pending_turn(self, session_id: UUID) -> InterviewTurn | None:
        stmt: Select[tuple[InterviewTurn]] = (
            select(InterviewTurn)
            .where(
                and_(
                    InterviewTurn.session_id == session_id,
                    InterviewTurn.candidate_message.is_(None),
                )
            )
            .order_by(InterviewTurn.turn_index.desc())
        )
        return await self.session.scalar(stmt)

    async def create_turn(self, turn: InterviewTurn) -> InterviewTurn:
        self.session.add(turn)
        await self.session.flush()
        return turn

    async def get_summary(self, session_id: UUID) -> InterviewSummary | None:
        stmt: Select[tuple[InterviewSummary]] = select(InterviewSummary).where(
            InterviewSummary.session_id == session_id
        )
        return await self.session.scalar(stmt)

    async def upsert_summary(self, summary: InterviewSummary) -> InterviewSummary:
        existing = await self.get_summary(summary.session_id)
        if existing is None:
            self.session.add(summary)
            await self.session.flush()
            return summary

        existing.final_score = summary.final_score
        existing.recommendation = summary.recommendation
        existing.strengths = summary.strengths
        existing.improvement_areas = summary.improvement_areas
        existing.summary = summary.summary
        await self.session.flush()
        return existing

    async def get_latest_summary_for_user(self, user_id: UUID) -> InterviewSummary | None:
        stmt: Select[tuple[InterviewSummary]] = (
            select(InterviewSummary)
            .join(InterviewSession, InterviewSummary.session_id == InterviewSession.id)
            .where(InterviewSession.user_id == user_id)
            .order_by(desc(InterviewSummary.created_at))
        )
        return await self.session.scalar(stmt)

