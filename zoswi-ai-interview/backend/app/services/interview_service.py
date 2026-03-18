import uuid
from dataclasses import dataclass
from time import perf_counter

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.metrics import metrics_store
from app.models.interview import InterviewStatus, TranscriptSpeaker
from app.repositories.interview_repository import InterviewRepository
from app.schemas.interview import (
    AIQuestionItem,
    CandidateResponseItem,
    EvaluationSignalsPayload,
    InterviewResultResponse,
    StartInterviewRequest,
    StartInterviewResponse,
    TranscriptItem,
)
from app.services.ai_service import AIService
from app.services.interview_engine import InterviewEngine
from app.services.scoring_engine import ScoringEngine

settings = get_settings()


@dataclass
class LiveTurnResult:
    session_id: uuid.UUID
    candidate_transcript: str
    next_question_text: str
    question_order: int
    signals: dict
    ai_audio_bytes: bytes
    completed: bool


class InterviewService:
    def __init__(
        self,
        repository: InterviewRepository,
        ai_service: AIService,
        interview_engine: InterviewEngine,
        scoring_engine: ScoringEngine,
    ):
        self.repository = repository
        self.ai_service = ai_service
        self.interview_engine = interview_engine
        self.scoring_engine = scoring_engine

    async def start_interview(
        self,
        payload: StartInterviewRequest,
        interview_type: str = "mixed",
        owner_user_id: str = "",
        org_id: str = "",
        resume_text: str = "",
    ) -> StartInterviewResponse:
        normalized_type = self._normalize_interview_type(interview_type)
        detected_domain = self.interview_engine.detect_domain(role=payload.role, resume_text=resume_text)
        session = await self.repository.create_session(
            candidate_name=payload.candidate_name,
            role=payload.role,
            interview_type=normalized_type,
            max_turns=settings.max_questions_per_interview,
            owner_user_id=owner_user_id,
            org_id=org_id,
            domain=detected_domain,
        )
        plan_state = self.interview_engine.build_plan(role=payload.role, resume_text=resume_text)
        await self.repository.create_or_update_plan(
            session_id=session.id,
            detected_domain=plan_state.detected_domain,
            items=plan_state.items,
            coverage_policy={
                "required_competencies": [item.get("competency_key") for item in plan_state.items],
                "must_cover": ["practical_implementation", "debugging", "architecture", "tradeoff_reasoning"],
            },
        )

        opening_question = await self.ai_service.generate_opening_question(
            payload.role,
            db=self.repository.db,
            session_seed=str(session.id),
            interview_type=normalized_type,
        )
        await self.repository.set_current_question(session, opening_question)
        await self.repository.add_ai_question(session.id, order=1, text=opening_question)
        await self.repository.add_transcript(
            session_id=session.id,
            speaker=TranscriptSpeaker.ai,
            text=opening_question,
            sequence_no=1,
        )
        await self.repository.set_transcript_history(session, [{"speaker": "ai", "text": opening_question}])
        await self.repository.commit()

        return StartInterviewResponse(
            session_id=session.id,
            websocket_path="/ws/interview",
            opening_question=opening_question,
            interview_type=normalized_type,
            interview_duration_seconds=settings.interview_duration_seconds,
            max_turns=session.max_turns,
        )

    async def process_live_turn(
        self,
        session_id: uuid.UUID,
        audio_bytes: bytes,
        mime_type: str = "audio/webm",
        interview_type: str = "mixed",
    ) -> LiveTurnResult:
        turn_started = perf_counter()
        normalized_type = self._normalize_interview_type(interview_type)
        session = await self.repository.get_session(session_id)
        if session is None:
            raise AppError(status_code=404, message="Interview session not found.")
        if session.status == InterviewStatus.completed:
            raise AppError(status_code=400, message="Interview session already completed.")
        plan_items_db = await self.repository.get_plan_items(session_id)
        if not plan_items_db:
            built_plan = self.interview_engine.build_plan(role=session.role, resume_text="")
            await self.repository.create_or_update_plan(
                session_id=session_id,
                detected_domain=built_plan.detected_domain,
                items=built_plan.items,
                coverage_policy={"must_cover": ["practical_implementation", "debugging", "architecture", "tradeoff_reasoning"]},
            )
            plan_items_db = await self.repository.get_plan_items(session_id)
        plan_items = [
            {
                "competency_key": item.competency_key,
                "target_turns": item.target_turns,
                "covered_turns": item.covered_turns,
                "priority": item.priority,
            }
            for item in plan_items_db
        ]

        current_question = await self.repository.get_latest_ai_question(session_id)
        current_question_id = current_question.id if current_question else None
        current_question_text = current_question.question_text if current_question else session.current_question

        transcript = await self.ai_service.transcribe_audio_bytes(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            db=self.repository.db,
        )
        if transcript.startswith("Audio could not") or transcript.startswith("Audio transcription"):
            metrics_store.increment_stt_failure()
            retry_prompt = "I could not hear that clearly. Please answer the same question again."
            sequence_start = await self.repository.get_next_transcript_sequence(session_id)
            await self.repository.add_transcript(
                session_id=session_id,
                speaker=TranscriptSpeaker.candidate,
                text=transcript,
                sequence_no=sequence_start,
            )
            await self.repository.add_transcript(
                session_id=session_id,
                speaker=TranscriptSpeaker.ai,
                text=retry_prompt,
                sequence_no=sequence_start + 1,
            )

            history = list(session.transcript_history or [])
            history.append({"speaker": "candidate", "text": transcript})
            history.append({"speaker": "ai", "text": retry_prompt})
            await self.repository.set_transcript_history(session, history)
            await self.repository.set_current_question(session, current_question_text)
            await self.repository.commit()

            ai_audio = await self.ai_service.synthesize_speech(retry_prompt, db=self.repository.db)
            existing_signals = session.evaluation_signals or {}
            signals = {
                "technical_accuracy": float(existing_signals.get("technical_accuracy", 0.0)),
                "communication_clarity": float(existing_signals.get("communication_clarity", 0.0)),
                "confidence": float(existing_signals.get("confidence", 0.0)),
                "overall_rating": float(existing_signals.get("overall_rating", 0.0)),
                "summary_text": str(existing_signals.get("summary_text", "Waiting for a clear answer.")),
            }
            return LiveTurnResult(
                session_id=session_id,
                candidate_transcript=transcript,
                next_question_text=retry_prompt,
                question_order=(current_question.question_order if current_question else session.turn_count + 1),
                signals=signals,
                ai_audio_bytes=ai_audio,
                completed=False,
            )

        response_order = session.turn_count + 1
        await self.repository.add_candidate_response(
            session_id=session_id,
            question_id=current_question_id,
            order=response_order,
            transcript_text=transcript,
        )

        sequence_start = await self.repository.get_next_transcript_sequence(session_id)
        await self.repository.add_transcript(
            session_id=session_id,
            speaker=TranscriptSpeaker.candidate,
            text=transcript,
            sequence_no=sequence_start,
        )

        history = list(session.transcript_history or [])
        history.append({"speaker": "candidate", "text": transcript})
        answer_quality_ok, answer_quality_score = self.interview_engine.assess_answer_quality(transcript)
        target_competency = self.interview_engine.select_next_competency(plan_items)
        turn = await self.ai_service.generate_next_question_and_evaluation(
            role=session.role,
            current_question=current_question_text,
            candidate_answer=transcript,
            transcript_history=history,
            db=self.repository.db,
            interview_type=normalized_type,
        )
        is_follow_up = self.interview_engine.should_follow_up(answer_quality_ok, answer_quality_score)
        if is_follow_up:
            turn["next_question"] = self._build_follow_up_question(target_competency, current_question_text)
            turn["summary_text"] = (
                f"{turn['summary_text']} Follow-up was selected due to low answer quality ({answer_quality_score})."
            ).strip()

        question_order = response_order + 1
        next_question = turn["next_question"]
        previous_ai_questions = [item.get("text", "") for item in history if item.get("speaker") == "ai"]
        if self.interview_engine.is_repeated_question(next_question, [str(item) for item in previous_ai_questions]):
            next_question = self._build_fallback_competency_question(session.role, target_competency)

        plan_items = self.interview_engine.update_coverage(plan_items, target_competency)
        coverage_reached = self.interview_engine.coverage_reached(plan_items)
        completed = response_order >= session.max_turns or coverage_reached
        next_question = (
            "Thank you for your time. This concludes the live interview."
            if completed
            else next_question
        )
        await self.repository.add_ai_question(session_id=session_id, order=question_order, text=next_question)
        await self.repository.add_transcript(
            session_id=session_id,
            speaker=TranscriptSpeaker.ai,
            text=next_question,
            sequence_no=sequence_start + 1,
        )
        history.append({"speaker": "ai", "text": next_question})

        await self.repository.set_transcript_history(session, history)
        await self.repository.set_current_question(session, next_question)
        await self.repository.increment_turn(session)
        await self.repository.create_or_update_plan(
            session_id=session_id,
            detected_domain=str(session.domain or ""),
            items=plan_items,
            coverage_policy={"must_cover": ["practical_implementation", "debugging", "architecture", "tradeoff_reasoning"]},
        )
        await self.repository.set_evaluation_signals(
            session,
            {
                "technical_accuracy": turn["technical_accuracy"],
                "communication_clarity": turn["communication_clarity"],
                "confidence": turn["confidence"],
                "overall_rating": turn["overall_rating"],
                "summary_text": turn["summary_text"],
                "target_competency": target_competency,
                "answer_quality_score": answer_quality_score,
            },
        )
        await self.repository.upsert_evaluation_summary(
            session_id=session_id,
            technical_accuracy=turn["technical_accuracy"],
            communication_clarity=turn["communication_clarity"],
            confidence=turn["confidence"],
            overall_rating=turn["overall_rating"],
            summary_text=turn["summary_text"],
            signals_json=session.evaluation_signals,
        )
        latency_ms = int((perf_counter() - turn_started) * 1000)
        turn_row = await self.repository.upsert_turn(
            session_id=session_id,
            question_id=current_question_id,
            turn_no=response_order,
            competency_key=target_competency,
            candidate_transcript=transcript,
            answer_quality_score=answer_quality_score,
            is_follow_up=is_follow_up,
            latency_ms=latency_ms,
            stt_confidence=1.0 if answer_quality_ok else 0.4,
        )
        turn_score = self.scoring_engine.score_turn(
            transcript_text=transcript,
            evaluation_signals={
                "technical_accuracy": turn["technical_accuracy"],
                "communication_clarity": turn["communication_clarity"],
                "confidence": turn["confidence"],
            },
            answer_quality_score=answer_quality_score,
            integrity_signal_count=0,
            competency_key=target_competency,
        )
        await self.repository.upsert_turn_score(
            turn_id=turn_row.id,
            technical_correctness=turn_score.technical_correctness,
            problem_solving_debugging=turn_score.problem_solving_debugging,
            architecture_design=turn_score.architecture_design,
            communication_clarity=turn_score.communication_clarity,
            tradeoff_reasoning=turn_score.tradeoff_reasoning,
            professional_integrity=turn_score.professional_integrity,
            confidence_score=turn_score.confidence_score,
            weighted_score=turn_score.weighted_score,
            evidence_snippet=turn_score.evidence_snippet,
            coverage_update=turn_score.coverage_update,
        )

        if completed:
            await self.repository.complete_session(session)
            stored_scores = await self.repository.list_turn_scores(session_id)
            synthesized = self.scoring_engine.summarize_final_assessment(
                [
                    self.scoring_engine.score_turn(
                        transcript_text=str(item.evidence_snippet or ""),
                        evaluation_signals={
                            "technical_accuracy": item.technical_correctness,
                            "communication_clarity": item.communication_clarity,
                            "confidence": item.confidence_score,
                        },
                        answer_quality_score=0.7,
                        integrity_signal_count=0,
                        competency_key=str((item.coverage_update or {}).get("competency_key", "")),
                    )
                    for item in stored_scores
                ]
            )
            await self.repository.upsert_final_assessment(
                session_id=session_id,
                overall_score=float(synthesized.get("overall_score", 0.0)),
                competency_coverage=float(synthesized.get("competency_coverage", 0.0)),
                strengths=[str(item) for item in synthesized.get("strengths", [])],
                weaknesses=[str(item) for item in synthesized.get("weaknesses", [])],
                recommendation=str(synthesized.get("recommendation", "No Hire")),
                summary_text=str(turn.get("summary_text", "")).strip(),
            )

        await self.repository.commit()
        metrics_store.increment_turn_completion()
        metrics_store.record_interview_latency(int((perf_counter() - turn_started) * 1000))

        ai_audio = await self.ai_service.synthesize_speech(next_question, db=self.repository.db)
        return LiveTurnResult(
            session_id=session_id,
            candidate_transcript=transcript,
            next_question_text=next_question,
            question_order=question_order,
            signals={
                "technical_accuracy": turn["technical_accuracy"],
                "communication_clarity": turn["communication_clarity"],
                "confidence": turn["confidence"],
                "overall_rating": turn["overall_rating"],
                "summary_text": turn["summary_text"],
                "target_competency": target_competency,
                "answer_quality_score": answer_quality_score,
            },
            ai_audio_bytes=ai_audio,
            completed=completed,
        )

    async def end_session(self, session_id: uuid.UUID) -> None:
        session = await self.repository.get_session(session_id)
        if session and session.status != InterviewStatus.completed:
            await self.repository.complete_session(session)
            await self.repository.commit()

    async def get_interview_result(self, session_id: uuid.UUID) -> InterviewResultResponse:
        session = await self.repository.get_session_detail(session_id)
        if session is None:
            raise AppError(status_code=404, message="Interview session not found.")

        evaluation = session.evaluation_summary
        return InterviewResultResponse(
            session_id=session.id,
            candidate_name=session.candidate_name,
            role=session.role,
            interview_type=session.interview_type,
            status=session.status,
            turn_count=session.turn_count,
            max_turns=session.max_turns,
            current_question=session.current_question,
            evaluation_signals=session.evaluation_signals,
            started_at=session.started_at,
            ended_at=session.ended_at,
            transcripts=[
                TranscriptItem(
                    speaker=item.speaker,
                    text=item.message_text,
                    sequence_no=item.sequence_no,
                    created_at=item.created_at,
                )
                for item in sorted(session.transcripts, key=lambda row: row.sequence_no)
            ],
            ai_questions=[
                AIQuestionItem(
                    id=item.id,
                    question_order=item.question_order,
                    question_text=item.question_text,
                    created_at=item.created_at,
                )
                for item in sorted(session.ai_questions, key=lambda row: row.question_order)
            ],
            candidate_responses=[
                CandidateResponseItem(
                    id=item.id,
                    response_order=item.response_order,
                    transcript_text=item.transcript_text,
                    created_at=item.created_at,
                )
                for item in sorted(session.candidate_responses, key=lambda row: row.response_order)
            ],
            evaluation_summary=(
                EvaluationSignalsPayload(
                    technical_accuracy=evaluation.technical_accuracy,
                    communication_clarity=evaluation.communication_clarity,
                    confidence=evaluation.confidence,
                    overall_rating=evaluation.overall_rating,
                    summary_text=evaluation.summary_text,
                )
                if evaluation
                else None
            ),
        )

    @staticmethod
    def _build_follow_up_question(competency_key: str, current_question: str) -> str:
        if competency_key == "debugging":
            return "Could you walk through the exact debugging steps and signals you would check first?"
        if competency_key == "architecture":
            return "Can you justify your architecture choice with clear trade-offs and failure scenarios?"
        if competency_key == "tradeoff_reasoning":
            return "What trade-offs did you make, and why did you prioritize that option?"
        return f"Please expand your previous answer with concrete implementation details for: {current_question}"

    @staticmethod
    def _build_fallback_competency_question(role: str, competency_key: str) -> str:
        if competency_key == "debugging":
            return f"For this {role} role, describe a production bug you diagnosed and how you isolated root cause."
        if competency_key == "architecture":
            return f"For this {role} role, explain a system design decision and how it scales under load."
        if competency_key == "tradeoff_reasoning":
            return f"For this {role} role, describe a key trade-off you made between speed, quality, and reliability."
        return f"For this {role} role, describe how you would implement a feature end to end in production."

    @staticmethod
    def _normalize_interview_type(interview_type: str) -> str:
        cleaned = str(interview_type or "").strip().lower().replace(" ", "_").replace("-", "_")
        if cleaned in {"technical", "behavioral"}:
            return cleaned
        if cleaned == "behavioural":
            return "behavioral"
        return "mixed"
