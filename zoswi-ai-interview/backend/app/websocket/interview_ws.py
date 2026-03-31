from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
import structlog

from app.core.exceptions import AuthenticationError, PlatformException
from app.core.security import decode_token
from app.db.session import SessionLocal
from app.schemas.ws import WSClientMessage
from app.services.interview_session_service import InterviewSessionService
from app.websocket.connection_manager import ConnectionManager
from app.core.redis import redis_client

logger = structlog.get_logger(__name__)
manager = ConnectionManager()


async def interview_ws_endpoint(websocket: WebSocket, session_id: UUID) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    try:
        claims = decode_token(token)
        if claims.type != "access":
            raise AuthenticationError("Access token required")
        user_id = UUID(claims.sub)
    except Exception:
        await websocket.close(code=1008)
        return

    await manager.connect(session_id=session_id, websocket=websocket)

    try:
        async with SessionLocal() as session:
            interview_service = InterviewSessionService(session, redis_client=redis_client)
            while True:
                incoming = await websocket.receive_json()
                message = WSClientMessage.model_validate(incoming)

                if message.type == "ping":
                    await manager.send_json(
                        session_id=session_id,
                        websocket=websocket,
                        payload={"type": "pong", "payload": {"session_id": str(session_id)}},
                    )
                    continue

                if message.type == "start":
                    started = await interview_service.start_session(user_id=user_id, session_id=session_id)
                    await manager.send_json(
                        session_id=session_id,
                        websocket=websocket,
                        payload={"type": "session_started", "payload": started.model_dump(mode="json")},
                    )
                    continue

                if message.type == "respond":
                    if not message.answer:
                        await manager.send_json(
                            session_id=session_id,
                            websocket=websocket,
                            payload={
                                "type": "error",
                                "payload": {
                                    "code": "missing_answer",
                                    "message": "answer is required for respond message type",
                                },
                            },
                        )
                        continue
                    response = await interview_service.respond(
                        user_id=user_id,
                        session_id=session_id,
                        answer=message.answer,
                    )
                    await manager.send_json(
                        session_id=session_id,
                        websocket=websocket,
                        payload={"type": "turn_processed", "payload": response.model_dump(mode="json")},
                    )
    except WebSocketDisconnect:
        manager.disconnect(session_id=session_id, websocket=websocket)
    except PlatformException as exc:
        logger.warning("ws_platform_exception", code=exc.code, message=exc.message)
        await websocket.send_json(
            {
                "type": "error",
                "payload": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            }
        )
        manager.disconnect(session_id=session_id, websocket=websocket)
    except Exception as exc:
        logger.exception("ws_unhandled_exception", error=str(exc))
        await websocket.send_json(
            {
                "type": "error",
                "payload": {
                    "code": "internal_server_error",
                    "message": "Unexpected websocket server failure",
                },
            }
        )
        manager.disconnect(session_id=session_id, websocket=websocket)

