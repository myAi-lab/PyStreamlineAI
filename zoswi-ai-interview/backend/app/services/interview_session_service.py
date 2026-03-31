import json
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas import TurnEvaluationAIOutput
from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.candidate_profile import CandidateProfile
from app.models.enums import InterviewStatus
from app.models.interview import InterviewSession, InterviewSummary, InterviewTurn
from app.repositories.audit_repository import AuditRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.interview_repository import InterviewRepository
from app.schemas.interview import (
    InterviewRespondResponse,
    InterviewSessionCreateRequest,
    InterviewSessionDetailResponse,
    InterviewSessionResponse,
    InterviewStartResponse,
    InterviewSummaryResponse,
    InterviewTurnResponse,
    TurnEvaluationResponse,
)
from app.services.interview_engine_service import InterviewEngineService
from app.services.scoring_engine_service import ScoringEngineService
from app.utils.time import utcnow


class InterviewSessionService:
    def __init__(self, session: AsyncSession, redis_client: Redis | None = None) -> None:
        self.session = session
        self.redis = redis_client
        self.settings = get_settings()
        self.repo = InterviewRepository(session)
        self.candidate_repo = CandidateRepository(session)
        self.audit_repo = AuditRepository(session)
        self.engine = InterviewEngineService()
        self.scoring = ScoringEngineService()

    async def create_session(
        self,
        *,
        user_id: UUID,
        payload: InterviewSessionCreateRequest,
    ) -> InterviewSessionResponse:
        session_model = InterviewSession(
            user_id=user_id,
            role_target=payload.role_target.strip(),
            status=InterviewStatus.CREATED,
            session_mode=payload.session_mode,
        )
        await self.repo.create_session(session_model)
        await self.audit_repo.create(
            AuditLog(
                entity_type="interview_session",
                entity_id=str(session_model.id),
                event_type="session_created",
                payload={"role_target": payload.role_target, "mode": payload.session_mode.value},
            )
        )
        await self.session.commit()
        await self.session.refresh(session_model)
        await self._save_runtime_state(session_model.id, {"status": session_model.status.value, "turns": 0})
        return InterviewSessionResponse.model_validate(session_model)

    async def list_sessions(self, user_id: UUID) -> list[InterviewSessionResponse]:
        sessions = await self.repo.list_sessions_for_user(user_id)
        return [InterviewSessionResponse.model_validate(item) for item in sessions]

    async def get_session_detail(self, *, user_id: UUID, session_id: UUID) -> InterviewSessionDetailResponse:
        session_model = await self._get_session_for_user(user_id=user_id, session_id=session_id)
        turns = await self.repo.list_turns(session_id)
        summary = await self.repo.get_summary(session_id)
        return InterviewSessionDetailResponse(
            session=InterviewSessionResponse.model_validate(session_model),
            turns=[InterviewTurnResponse.model_validate(turn) for turn in turns],
            summary=InterviewSummaryResponse.model_validate(summary) if summary else None,
        )

    async def start_session(self, *, user_id: UUID, session_id: UUID) -> InterviewStartResponse:
        session_model = await self._get_session_for_user(user_id=user_id, session_id=session_id)
        if session_model.status not in {
            InterviewStatus.CREATED,
            InterviewStatus.READY,
            InterviewStatus.PAUSED,
            InterviewStatus.ACTIVE,
        }:
            raise ValidationError("Session cannot be started from current state")

        existing_pending = await self.repo.get_pending_turn(session_model.id)
        if existing_pending is not None:
            session_model.status = InterviewStatus.ACTIVE
            if session_model.started_at is None:
                session_model.started_at = utcnow()
            await self.session.commit()
            return InterviewStartResponse(
                session=InterviewSessionResponse.model_validate(session_model),
                first_turn=InterviewTurnResponse.model_validate(existing_pending),
                is_complete=False,
            )

        turns = await self.repo.list_turns(session_model.id)
        profile = await self.candidate_repo.get_by_user_id(user_id)
        question = await self.engine.generate_next_question(
            session=session_model,
            turns=turns,
            profile=profile,
        )
        next_index = len(turns) + 1
        first_turn = InterviewTurn(
            session_id=session_model.id,
            turn_index=next_index,
            interviewer_message=question.interviewer_message,
            model_feedback={
                "question_tone": question.tone,
                "question_action": question.next_action,
            },
        )
        await self.repo.create_turn(first_turn)
        session_model.status = InterviewStatus.ACTIVE
        if session_model.started_at is None:
            session_model.started_at = utcnow()
        await self.audit_repo.create(
            AuditLog(
                entity_type="interview_session",
                entity_id=str(session_model.id),
                event_type="session_started",
                payload={"first_turn": next_index},
            )
        )
        await self.session.commit()
        await self.session.refresh(first_turn)
        await self.session.refresh(session_model)
        await self._save_runtime_state(
            session_model.id,
            {
                "status": session_model.status.value,
                "turns": next_index,
                "last_question": first_turn.interviewer_message,
            },
        )
        return InterviewStartResponse(
            session=InterviewSessionResponse.model_validate(session_model),
            first_turn=InterviewTurnResponse.model_validate(first_turn),
            is_complete=False,
        )

    async def respond(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        answer: str,
    ) -> InterviewRespondResponse:
        session_model = await self._get_session_for_user(user_id=user_id, session_id=session_id)
        if session_model.status != InterviewStatus.ACTIVE:
            raise ValidationError("Session is not active")

        pending_turn = await self.repo.get_pending_turn(session_id)
        if pending_turn is None:
            raise ValidationError("No pending interview question to answer")

        pending_turn.candidate_message = answer.strip()
        profile = await self.candidate_repo.get_by_user_id(user_id)
        previous_turns = await self.repo.list_turns(session_id)
        evaluation = await self.scoring.evaluate_turn(
            session=session_model,
            question=pending_turn.interviewer_message,
            answer=pending_turn.candidate_message,
            prior_turns=previous_turns,
            experience_level=self._infer_experience_level(profile),
        )
        next_step_guidance = self._derive_next_step_guidance(evaluation)
        pending_turn.model_feedback = {
            "strengths": evaluation.strengths,
            "weaknesses": evaluation.weaknesses,
            "feedback": evaluation.feedback,
            "next_step_guidance": next_step_guidance,
        }
        pending_turn.score_overall = evaluation.score_overall
        pending_turn.score_communication = evaluation.score_communication
        pending_turn.score_technical = evaluation.score_technical
        pending_turn.score_confidence = evaluation.score_confidence

        turns_after_eval = await self.repo.list_turns(session_id)
        scored_count = len([turn for turn in turns_after_eval if turn.candidate_message])
        should_complete = scored_count >= self.settings.interview_max_turns
        next_turn: InterviewTurn | None = None

        if not should_complete:
            question = await self.engine.generate_next_question(
                session=session_model,
                turns=turns_after_eval,
                profile=profile,
            )
            should_complete = question.next_action == "conclude"
            if not should_complete:
                next_turn = InterviewTurn(
                    session_id=session_model.id,
                    turn_index=len(turns_after_eval) + 1,
                    interviewer_message=question.interviewer_message,
                    model_feedback={
                        "question_tone": question.tone,
                        "question_action": question.next_action,
                    },
                )
                await self.repo.create_turn(next_turn)

        summary_payload: InterviewSummary | None = None
        if should_complete:
            session_model.status = InterviewStatus.COMPLETED
            session_model.ended_at = utcnow()
            completed_turns = await self.repo.list_turns(session_id)
            summary_output = await self.scoring.summarize_session(
                session=session_model,
                turns=completed_turns,
            )
            summary_payload = InterviewSummary(
                session_id=session_model.id,
                final_score=summary_output.final_score,
                recommendation=summary_output.recommendation,
                strengths=summary_output.strengths,
                improvement_areas=summary_output.improvement_areas,
                summary=summary_output.summary,
            )
            await self.repo.upsert_summary(summary_payload)
            await self.audit_repo.create(
                AuditLog(
                    entity_type="interview_session",
                    entity_id=str(session_model.id),
                    event_type="session_completed",
                    payload={"final_score": summary_output.final_score},
                )
            )

        await self.session.commit()
        await self.session.refresh(session_model)
        await self.session.refresh(pending_turn)
        if next_turn is not None:
            await self.session.refresh(next_turn)
        if summary_payload is not None:
            await self.session.refresh(summary_payload)

        await self._save_runtime_state(
            session_model.id,
            {
                "status": session_model.status.value,
                "turns": len(turns_after_eval) + (1 if next_turn else 0),
                "last_score": evaluation.score_overall,
            },
        )

        return InterviewRespondResponse(
            session=InterviewSessionResponse.model_validate(session_model),
            evaluated_turn=InterviewTurnResponse.model_validate(pending_turn),
            evaluation=TurnEvaluationResponse(
                turn_id=pending_turn.id,
                score_overall=evaluation.score_overall,
                score_communication=evaluation.score_communication,
                score_technical=evaluation.score_technical,
                score_confidence=evaluation.score_confidence,
                strengths=evaluation.strengths,
                weaknesses=evaluation.weaknesses,
                feedback=evaluation.feedback,
                next_step_guidance=next_step_guidance,
            ),
            next_turn=InterviewTurnResponse.model_validate(next_turn) if next_turn else None,
            is_complete=session_model.status == InterviewStatus.COMPLETED,
        )

    async def get_summary(self, *, user_id: UUID, session_id: UUID) -> InterviewSummaryResponse:
        session_model = await self._get_session_for_user(user_id=user_id, session_id=session_id)
        summary = await self.repo.get_summary(session_model.id)
        if summary is None:
            raise NotFoundError("Interview summary is not available yet")
        return InterviewSummaryResponse.model_validate(summary)

    async def _get_session_for_user(self, *, user_id: UUID, session_id: UUID) -> InterviewSession:
        session_model = await self.repo.get_session_for_user(user_id=user_id, session_id=session_id)
        if session_model is None:
            raise NotFoundError("Interview session not found")
        return session_model

    async def _save_runtime_state(self, session_id: UUID, payload: dict) -> None:
        if self.redis is None:
            return
        await self.redis.setex(f"interview:state:{session_id}", 3600, json.dumps(payload))

    @staticmethod
    def _infer_experience_level(profile: CandidateProfile | None) -> str:
        years = getattr(profile, "years_experience", None)
        if years is None:
            return "mid"
        if years <= 2:
            return "junior"
        if years <= 6:
            return "mid"
        return "senior"

    @staticmethod
    def _derive_next_step_guidance(evaluation: TurnEvaluationAIOutput) -> str:
        for weakness in evaluation.weaknesses:
            cleaned = str(weakness).strip()
            if cleaned:
                return cleaned
        feedback = " ".join(str(evaluation.feedback).split())
        if feedback:
            parts = [part.strip() for part in feedback.split(".") if part.strip()]
            if parts:
                last = parts[-1]
                return last if last.endswith(".") else f"{last}."
        return "Use a clearer structure with one concrete decision and measurable impact."
