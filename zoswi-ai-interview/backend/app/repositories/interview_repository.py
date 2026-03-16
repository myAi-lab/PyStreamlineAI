import uuid
from datetime import datetime, timezone

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.interview import (
    AIQuestion,
    CandidateResponse,
    ConversationTranscript,
    EvaluationSummary,
    InterviewSession,
    InterviewStatus,
    TranscriptSpeaker,
)


class InterviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        candidate_name: str,
        role: str,
        max_turns: int,
        interview_type: str = "mixed",
    ) -> InterviewSession:
        session = InterviewSession(
            candidate_name=candidate_name,
            role=role,
            interview_type=interview_type,
            max_turns=max_turns,
            status=InterviewStatus.in_progress,
            turn_count=0,
            current_question="",
            transcript_history=[],
            evaluation_signals={},
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session(self, session_id: uuid.UUID) -> InterviewSession | None:
        result = await self.db.execute(select(InterviewSession).where(InterviewSession.id == session_id))
        return result.scalar_one_or_none()

    async def add_ai_question(self, session_id: uuid.UUID, order: int, text: str) -> AIQuestion:
        question = AIQuestion(session_id=session_id, question_order=order, question_text=text)
        self.db.add(question)
        await self.db.flush()
        return question

    async def get_ai_question(self, question_id: uuid.UUID) -> AIQuestion | None:
        result = await self.db.execute(select(AIQuestion).where(AIQuestion.id == question_id))
        return result.scalar_one_or_none()

    async def get_latest_ai_question(self, session_id: uuid.UUID) -> AIQuestion | None:
        statement = (
            select(AIQuestion)
            .where(AIQuestion.session_id == session_id)
            .order_by(AIQuestion.question_order.desc())
            .limit(1)
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def list_ai_questions(self, session_id: uuid.UUID) -> list[AIQuestion]:
        statement: Select[tuple[AIQuestion]] = (
            select(AIQuestion).where(AIQuestion.session_id == session_id).order_by(AIQuestion.question_order.asc())
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def add_candidate_response(
        self,
        session_id: uuid.UUID,
        question_id: uuid.UUID | None,
        order: int,
        transcript_text: str,
    ) -> CandidateResponse:
        response = CandidateResponse(
            session_id=session_id,
            question_id=question_id,
            response_order=order,
            transcript_text=transcript_text,
        )
        self.db.add(response)
        await self.db.flush()
        return response

    async def count_candidate_responses(self, session_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count(CandidateResponse.id)).where(CandidateResponse.session_id == session_id)
        )
        return int(result.scalar_one())

    async def list_candidate_responses(self, session_id: uuid.UUID) -> list[CandidateResponse]:
        statement: Select[tuple[CandidateResponse]] = (
            select(CandidateResponse)
            .where(CandidateResponse.session_id == session_id)
            .order_by(CandidateResponse.response_order.asc())
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def add_transcript(
        self,
        session_id: uuid.UUID,
        speaker: TranscriptSpeaker,
        text: str,
        sequence_no: int,
    ) -> ConversationTranscript:
        transcript = ConversationTranscript(
            session_id=session_id,
            speaker=speaker,
            message_text=text,
            sequence_no=sequence_no,
        )
        self.db.add(transcript)
        await self.db.flush()
        return transcript

    async def get_next_transcript_sequence(self, session_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.max(ConversationTranscript.sequence_no)).where(ConversationTranscript.session_id == session_id)
        )
        max_value = result.scalar_one_or_none()
        return 1 if max_value is None else int(max_value) + 1

    async def list_transcripts(self, session_id: uuid.UUID) -> list[ConversationTranscript]:
        statement: Select[tuple[ConversationTranscript]] = (
            select(ConversationTranscript)
            .where(ConversationTranscript.session_id == session_id)
            .order_by(ConversationTranscript.sequence_no.asc())
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def upsert_evaluation_summary(
        self,
        session_id: uuid.UUID,
        technical_accuracy: float,
        communication_clarity: float,
        confidence: float,
        overall_rating: float,
        summary_text: str,
        signals_json: dict,
    ) -> EvaluationSummary:
        existing = await self.get_evaluation_summary(session_id)
        if existing is None:
            existing = EvaluationSummary(
                session_id=session_id,
                technical_accuracy=technical_accuracy,
                communication_clarity=communication_clarity,
                confidence=confidence,
                overall_rating=overall_rating,
                summary_text=summary_text,
                signals_json=signals_json,
            )
            self.db.add(existing)
        else:
            existing.technical_accuracy = technical_accuracy
            existing.communication_clarity = communication_clarity
            existing.confidence = confidence
            existing.overall_rating = overall_rating
            existing.summary_text = summary_text
            existing.signals_json = signals_json

        await self.db.flush()
        return existing

    async def get_evaluation_summary(self, session_id: uuid.UUID) -> EvaluationSummary | None:
        result = await self.db.execute(select(EvaluationSummary).where(EvaluationSummary.session_id == session_id))
        return result.scalar_one_or_none()

    async def set_current_question(self, session: InterviewSession, text: str) -> None:
        session.current_question = text
        await self.db.flush()

    async def increment_turn(self, session: InterviewSession) -> None:
        session.turn_count += 1
        await self.db.flush()

    async def set_transcript_history(self, session: InterviewSession, history: list[dict]) -> None:
        session.transcript_history = history
        await self.db.flush()

    async def set_evaluation_signals(self, session: InterviewSession, signals: dict) -> None:
        session.evaluation_signals = signals
        await self.db.flush()

    async def complete_session(self, session: InterviewSession) -> None:
        session.status = InterviewStatus.completed
        session.ended_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def get_session_detail(self, session_id: uuid.UUID) -> InterviewSession | None:
        statement = (
            select(InterviewSession)
            .options(
                joinedload(InterviewSession.ai_questions),
                joinedload(InterviewSession.candidate_responses),
                joinedload(InterviewSession.transcripts),
                joinedload(InterviewSession.evaluation_summary),
            )
            .where(InterviewSession.id == session_id)
        )
        result = await self.db.execute(statement)
        return result.unique().scalar_one_or_none()

    async def commit(self) -> None:
        await self.db.commit()
