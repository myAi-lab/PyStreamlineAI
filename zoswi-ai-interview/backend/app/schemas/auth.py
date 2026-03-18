import uuid

from pydantic import BaseModel, Field


class WebSocketTokenRequest(BaseModel):
    session_id: uuid.UUID = Field(description="Interview session id bound to websocket token.")


class WebSocketTokenResponse(BaseModel):
    ws_token: str
    token_type: str = "Bearer"
    expires_in: int
    session_id: uuid.UUID
