import uuid
from datetime import datetime, timezone

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.interview import (
    AIQuestion,
    CandidateResponse,
    FinalAssessment,
    ConversationTranscript,
    EvaluationSummary,
    IntegrityEvent,
    InterviewPlan,
    InterviewPlanItem,
    InterviewSession,
    InterviewStatus,
    InterviewTurn,
    RecruiterReview,
    TranscriptSpeaker,
    TurnScore,
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
        owner_user_id: str = "",
        org_id: str = "",
        domain: str = "",
    ) -> InterviewSession:
        session = InterviewSession(
            candidate_name=candidate_name,
            role=role,
            owner_user_id=owner_user_id,
            org_id=org_id,
            domain=domain,
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

    async def create_or_update_plan(
        self,
        *,
        session_id: uuid.UUID,
        detected_domain: str,
        items: list[dict],
        coverage_policy: dict | None = None,
    ) -> InterviewPlan:
        existing = await self.db.execute(select(InterviewPlan).where(InterviewPlan.session_id == session_id))
        plan = existing.scalar_one_or_none()
        if plan is None:
            plan = InterviewPlan(
                session_id=session_id,
                detected_domain=detected_domain,
                coverage_policy=coverage_policy or {},
                status="active",
            )
            self.db.add(plan)
            await self.db.flush()
        else:
            plan.detected_domain = detected_domain
            plan.coverage_policy = coverage_policy or {}
            plan.status = "active"
            await self.db.flush()

        await self.db.execute(
            select(InterviewPlanItem).where(InterviewPlanItem.plan_id == plan.id)
        )
        await self.db.execute(
            InterviewPlanItem.__table__.delete().where(InterviewPlanItem.plan_id == plan.id)
        )
        await self.db.flush()

        for item in items:
            row = InterviewPlanItem(
                plan_id=plan.id,
                competency_key=str(item.get("competency_key", "")).strip(),
                target_turns=int(item.get("target_turns", 1) or 1),
                covered_turns=int(item.get("covered_turns", 0) or 0),
                priority=int(item.get("priority", 1) or 1),
            )
            self.db.add(row)
        await self.db.flush()
        return plan

    async def get_plan_items(self, session_id: uuid.UUID) -> list[InterviewPlanItem]:
        plan_result = await self.db.execute(select(InterviewPlan).where(InterviewPlan.session_id == session_id))
        plan = plan_result.scalar_one_or_none()
        if plan is None:
            return []
        rows = await self.db.execute(
            select(InterviewPlanItem).where(InterviewPlanItem.plan_id == plan.id).order_by(InterviewPlanItem.priority.asc())
        )
        return list(rows.scalars().all())

    async def upsert_turn(
        self,
        *,
        session_id: uuid.UUID,
        question_id: uuid.UUID | None,
        turn_no: int,
        competency_key: str,
        candidate_transcript: str,
        answer_quality_score: float,
        is_follow_up: bool,
        latency_ms: int = 0,
        stt_confidence: float = 0.0,
    ) -> InterviewTurn:
        row = InterviewTurn(
            session_id=session_id,
            question_id=question_id,
            turn_no=turn_no,
            competency_key=competency_key,
            candidate_transcript=candidate_transcript,
            answer_quality_score=answer_quality_score,
            is_follow_up=is_follow_up,
            latency_ms=latency_ms,
            stt_confidence=stt_confidence,
        )
        self.db.add(row)
        await self.db.flush()
        return row

    async def upsert_turn_score(
        self,
        *,
        turn_id: uuid.UUID,
        technical_correctness: float,
        problem_solving_debugging: float,
        architecture_design: float,
        communication_clarity: float,
        tradeoff_reasoning: float,
        professional_integrity: float,
        confidence_score: float,
        weighted_score: float,
        evidence_snippet: str,
        coverage_update: dict,
    ) -> TurnScore:
        existing_result = await self.db.execute(select(TurnScore).where(TurnScore.turn_id == turn_id))
        existing = existing_result.scalar_one_or_none()
        if existing is None:
            existing = TurnScore(
                turn_id=turn_id,
                technical_correctness=technical_correctness,
                problem_solving_debugging=problem_solving_debugging,
                architecture_design=architecture_design,
                communication_clarity=communication_clarity,
                tradeoff_reasoning=tradeoff_reasoning,
                professional_integrity=professional_integrity,
                confidence_score=confidence_score,
                weighted_score=weighted_score,
                evidence_snippet=evidence_snippet,
                coverage_update=coverage_update,
            )
            self.db.add(existing)
        else:
            existing.technical_correctness = technical_correctness
            existing.problem_solving_debugging = problem_solving_debugging
            existing.architecture_design = architecture_design
            existing.communication_clarity = communication_clarity
            existing.tradeoff_reasoning = tradeoff_reasoning
            existing.professional_integrity = professional_integrity
            existing.confidence_score = confidence_score
            existing.weighted_score = weighted_score
            existing.evidence_snippet = evidence_snippet
            existing.coverage_update = coverage_update
        await self.db.flush()
        return existing

    async def list_turn_scores(self, session_id: uuid.UUID) -> list[TurnScore]:
        rows = await self.db.execute(
            select(TurnScore)
            .join(InterviewTurn, InterviewTurn.id == TurnScore.turn_id)
            .where(InterviewTurn.session_id == session_id)
            .order_by(InterviewTurn.turn_no.asc())
        )
        return list(rows.scalars().all())

    async def upsert_final_assessment(
        self,
        *,
        session_id: uuid.UUID,
        overall_score: float,
        competency_coverage: float,
        strengths: list[str],
        weaknesses: list[str],
        recommendation: str,
        summary_text: str,
    ) -> FinalAssessment:
        existing_result = await self.db.execute(select(FinalAssessment).where(FinalAssessment.session_id == session_id))
        existing = existing_result.scalar_one_or_none()
        if existing is None:
            existing = FinalAssessment(
                session_id=session_id,
                overall_score=overall_score,
                competency_coverage=competency_coverage,
                strengths=strengths,
                weaknesses=weaknesses,
                recommendation=recommendation,
                summary_text=summary_text,
            )
            self.db.add(existing)
        else:
            existing.overall_score = overall_score
            existing.competency_coverage = competency_coverage
            existing.strengths = strengths
            existing.weaknesses = weaknesses
            existing.recommendation = recommendation
            existing.summary_text = summary_text
        await self.db.flush()
        return existing

    async def add_integrity_event(
        self,
        *,
        session_id: uuid.UUID,
        event_type: str,
        severity: float,
        details: dict | None = None,
        turn_id: uuid.UUID | None = None,
    ) -> IntegrityEvent:
        event = IntegrityEvent(
            session_id=session_id,
            turn_id=turn_id,
            event_type=event_type,
            severity=severity,
            details=details or {},
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def list_integrity_events(self, session_id: uuid.UUID) -> list[IntegrityEvent]:
        rows = await self.db.execute(
            select(IntegrityEvent).where(IntegrityEvent.session_id == session_id).order_by(IntegrityEvent.created_at.asc())
        )
        return list(rows.scalars().all())

    async def add_recruiter_review(
        self,
        *,
        session_id: uuid.UUID,
        reviewer_user_id: str,
        decision: str,
        notes: str,
        override_recommendation: bool = False,
    ) -> RecruiterReview:
        review = RecruiterReview(
            session_id=session_id,
            reviewer_user_id=reviewer_user_id,
            decision=decision,
            notes=notes,
            override_recommendation=override_recommendation,
        )
        self.db.add(review)
        await self.db.flush()
        return review

    async def list_recruiter_reviews(self, session_id: uuid.UUID) -> list[RecruiterReview]:
        rows = await self.db.execute(
            select(RecruiterReview).where(RecruiterReview.session_id == session_id).order_by(RecruiterReview.created_at.desc())
        )
        return list(rows.scalars().all())

    async def list_sessions_for_recruiter(
        self,
        *,
        role_filter: str = "",
        min_score: float | None = None,
        limit: int = 100,
    ) -> list[InterviewSession]:
        statement = select(InterviewSession).order_by(InterviewSession.created_at.desc()).limit(max(1, int(limit)))
        if str(role_filter).strip():
            statement = statement.where(InterviewSession.role.ilike(f"%{role_filter.strip()}%"))
        rows = await self.db.execute(statement)
        sessions = list(rows.scalars().all())
        if min_score is None:
            return sessions

        filtered: list[InterviewSession] = []
        for session in sessions:
            assessment_result = await self.db.execute(
                select(FinalAssessment).where(FinalAssessment.session_id == session.id)
            )
            assessment = assessment_result.scalar_one_or_none()
            if assessment and float(assessment.overall_score or 0.0) >= float(min_score):
                filtered.append(session)
        return filtered
