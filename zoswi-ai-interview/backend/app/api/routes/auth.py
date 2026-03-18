import uuid

from fastapi import APIRouter, Depends

from app.api.deps import get_current_auth_context
from app.core.auth import AuthContext, mint_ws_token
from app.schemas.auth import WebSocketTokenRequest, WebSocketTokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/ws-token", response_model=WebSocketTokenResponse)
async def create_websocket_token(
    payload: WebSocketTokenRequest,
    auth_ctx: AuthContext = Depends(get_current_auth_context),
) -> WebSocketTokenResponse:
    session_id = uuid.UUID(str(payload.session_id))
    token, expires_in = mint_ws_token(access_ctx=auth_ctx, session_id=session_id)
    return WebSocketTokenResponse(
        ws_token=token,
        expires_in=expires_in,
        session_id=session_id,
    )
