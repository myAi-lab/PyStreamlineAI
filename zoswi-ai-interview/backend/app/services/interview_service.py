import uuid
from dataclasses import dataclass

from app.core.config import get_settings
from app.core.exceptions import AppError
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
    def __init__(self, repository: InterviewRepository, ai_service: AIService):
        self.repository = repository
        self.ai_service = ai_service

    async def start_interview(
        self,
        payload: StartInterviewRequest,
        interview_type: str = "mixed",
    ) -> StartInterviewResponse:
        normalized_type = self._normalize_interview_type(interview_type)
        session = await self.repository.create_session(
            candidate_name=payload.candidate_name,
            role=payload.role,
            interview_type=normalized_type,
            max_turns=settings.max_questions_per_interview,
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
        normalized_type = self._normalize_interview_type(interview_type)
        session = await self.repository.get_session(session_id)
        if session is None:
            raise AppError(status_code=404, message="Interview session not found.")
        if session.status == InterviewStatus.completed:
            raise AppError(status_code=400, message="Interview session already completed.")

        current_question = await self.repository.get_latest_ai_question(session_id)
        current_question_id = current_question.id if current_question else None
        current_question_text = current_question.question_text if current_question else session.current_question

        transcript = await self.ai_service.transcribe_audio_bytes(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            db=self.repository.db,
        )
        if transcript.startswith("Audio could not") or transcript.startswith("Audio transcription"):
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
        turn = await self.ai_service.generate_next_question_and_evaluation(
            role=session.role,
            current_question=current_question_text,
            candidate_answer=transcript,
            transcript_history=history,
            db=self.repository.db,
            interview_type=normalized_type,
        )

        question_order = response_order + 1
        completed = response_order >= session.max_turns
        next_question = (
            "Thank you for your time. This concludes the live interview."
            if completed
            else turn["next_question"]
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
        await self.repository.set_evaluation_signals(
            session,
            {
                "technical_accuracy": turn["technical_accuracy"],
                "communication_clarity": turn["communication_clarity"],
                "confidence": turn["confidence"],
                "overall_rating": turn["overall_rating"],
                "summary_text": turn["summary_text"],
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

        if completed:
            await self.repository.complete_session(session)

        await self.repository.commit()

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
    def _normalize_interview_type(interview_type: str) -> str:
        cleaned = str(interview_type or "").strip().lower().replace(" ", "_").replace("-", "_")
        if cleaned in {"technical", "behavioral"}:
            return cleaned
        if cleaned == "behavioural":
            return "behavioral"
        return "mixed"
