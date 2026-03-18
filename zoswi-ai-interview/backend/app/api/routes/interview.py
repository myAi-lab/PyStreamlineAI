import base64
import json
import logging
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.deps import get_ai_service, get_interview_service
from app.core.db import SessionLocal
from app.core.exceptions import AppError
from app.repositories.interview_repository import InterviewRepository
from app.schemas.interview import InterviewResultResponse, StartInterviewRequest, StartInterviewResponse
from app.services.interview_service import InterviewService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["interview"])


def _normalize_interview_type(raw_value: str) -> str:
    cleaned = str(raw_value or "").strip().lower().replace(" ", "_").replace("-", "_")
    if cleaned in {"technical", "behavioral", "behavioural"}:
        return "behavioral" if cleaned == "behavioural" else cleaned
    return "mixed"


@router.post("/start-interview", response_model=StartInterviewResponse)
async def start_interview(
    payload: StartInterviewRequest,
    service: InterviewService = Depends(get_interview_service),
) -> StartInterviewResponse:
    interview_type = _normalize_interview_type(payload.interview_type)
    return await service.start_interview(payload, interview_type=interview_type)


@router.get("/interview-result", response_model=InterviewResultResponse)
async def get_interview_result(
    session_id: uuid.UUID,
    service: InterviewService = Depends(get_interview_service),
) -> InterviewResultResponse:
    return await service.get_interview_result(session_id=session_id)


@router.websocket("/ws/interview")
async def interview_websocket(websocket: WebSocket):
    await websocket.accept()
    ai_service = get_ai_service()

    active_session_id: uuid.UUID | None = None
    active_interview_type = "mixed"
    active_mime_type = "audio/webm"
    candidate_audio_buffer = bytearray()

    await websocket.send_json({"type": "connection_status", "status": "connected"})

    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                payload = json.loads(raw_message)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON payload."})
                continue

            message_type = payload.get("type")

            if message_type == "session_start":
                candidate_name = str(payload.get("candidate_name", "")).strip()
                role = str(payload.get("role", "Software Engineer")).strip() or "Software Engineer"
                interview_type = _normalize_interview_type(str(payload.get("interview_type", "mixed")))
                if len(candidate_name) < 2:
                    await websocket.send_json({"type": "error", "message": "candidate_name is required."})
                    continue

                async with SessionLocal() as db:
                    repository = InterviewRepository(db)
                    service = InterviewService(repository=repository, ai_service=ai_service)
                    start_response = await service.start_interview(
                        StartInterviewRequest(
                            candidate_name=candidate_name,
                            role=role,
                            interview_type=interview_type,
                        ),
                        interview_type=interview_type,
                    )
                    opening_audio = await ai_service.synthesize_speech(start_response.opening_question, db=db)
                active_session_id = start_response.session_id
                active_interview_type = interview_type
                candidate_audio_buffer.clear()

                await websocket.send_json(
                    {
                        "type": "session_started",
                        "session_id": str(start_response.session_id),
                        "opening_question": start_response.opening_question,
                        "interview_type": start_response.interview_type,
                        "max_turns": start_response.max_turns,
                        "interview_duration_seconds": start_response.interview_duration_seconds,
                    }
                )
                await websocket.send_json(
                    {
                        "type": "transcript",
                        "speaker": "ai",
                        "text": start_response.opening_question,
                    }
                )

                if opening_audio:
                    await websocket.send_json({"type": "connection_status", "status": "speaking"})
                    await websocket.send_json(
                        {
                            "type": "ai_audio",
                            "mime_type": "audio/mpeg",
                            "audio_base64": base64.b64encode(opening_audio).decode("utf-8"),
                        }
                    )
                await websocket.send_json({"type": "connection_status", "status": "listening"})
                continue

            if message_type == "audio_chunk":
                if active_session_id is None:
                    await websocket.send_json({"type": "error", "message": "Session not initialized."})
                    continue
                chunk_base64 = payload.get("chunk_base64")
                if not chunk_base64:
                    continue
                try:
                    candidate_audio_buffer.extend(base64.b64decode(chunk_base64))
                except Exception:
                    await websocket.send_json({"type": "error", "message": "Invalid audio chunk encoding."})
                    continue
                active_mime_type = str(payload.get("mime_type", active_mime_type))
                continue

            if message_type == "candidate_turn_end":
                if active_session_id is None:
                    await websocket.send_json({"type": "error", "message": "Session not initialized."})
                    continue
                if not candidate_audio_buffer:
                    await websocket.send_json({"type": "warning", "message": "No audio captured for this turn."})
                    continue

                await websocket.send_json({"type": "connection_status", "status": "thinking"})
                async with SessionLocal() as db:
                    repository = InterviewRepository(db)
                    service = InterviewService(repository=repository, ai_service=ai_service)
                    turn_result = await service.process_live_turn(
                        session_id=active_session_id,
                        audio_bytes=bytes(candidate_audio_buffer),
                        mime_type=active_mime_type,
                        interview_type=active_interview_type,
                    )
                candidate_audio_buffer.clear()

                await websocket.send_json(
                    {
                        "type": "transcript",
                        "speaker": "candidate",
                        "text": turn_result.candidate_transcript,
                    }
                )
                await websocket.send_json(
                    {
                        "type": "evaluation_signals",
                        **turn_result.signals,
                    }
                )
                await websocket.send_json(
                    {
                        "type": "next_question",
                        "question_text": turn_result.next_question_text,
                        "question_order": turn_result.question_order,
                    }
                )
                await websocket.send_json(
                    {
                        "type": "transcript",
                        "speaker": "ai",
                        "text": turn_result.next_question_text,
                    }
                )

                if turn_result.ai_audio_bytes:
                    await websocket.send_json({"type": "connection_status", "status": "speaking"})
                    await websocket.send_json(
                        {
                            "type": "ai_audio",
                            "mime_type": "audio/mpeg",
                            "audio_base64": base64.b64encode(turn_result.ai_audio_bytes).decode("utf-8"),
                        }
                    )

                if turn_result.completed:
                    await websocket.send_json(
                        {
                            "type": "session_complete",
                            "session_id": str(turn_result.session_id),
                            "signals": turn_result.signals,
                        }
                    )
                    await websocket.send_json({"type": "connection_status", "status": "completed"})
                else:
                    await websocket.send_json({"type": "connection_status", "status": "listening"})
                continue

            if message_type == "session_end":
                if active_session_id:
                    async with SessionLocal() as db:
                        repository = InterviewRepository(db)
                        service = InterviewService(repository=repository, ai_service=ai_service)
                        await service.end_session(active_session_id)
                await websocket.send_json({"type": "session_complete", "session_id": str(active_session_id or "")})
                await websocket.send_json({"type": "connection_status", "status": "closed"})
                await websocket.close()
                return

            await websocket.send_json({"type": "error", "message": f"Unsupported event type: {message_type}"})

    except WebSocketDisconnect:
        logger.info("Interview websocket disconnected. session_id=%s", active_session_id)
    except AppError as exc:
        try:
            await websocket.send_json({"type": "error", "message": exc.message, "details": exc.details})
        except WebSocketDisconnect:
            logger.info("Client disconnected before AppError could be sent. session_id=%s", active_session_id)
    except Exception as exc:
        error_type = type(exc).__name__
        error_text = str(exc).strip()
        detail = error_type if not error_text else f"{error_type}: {error_text}"
        logger.exception("Unhandled websocket error: %s", detail)
        try:
            await websocket.send_json({"type": "error", "message": f"Internal websocket error ({detail[:240]})."})
        except WebSocketDisconnect:
            logger.info("Client disconnected before internal error could be sent. session_id=%s", active_session_id)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
