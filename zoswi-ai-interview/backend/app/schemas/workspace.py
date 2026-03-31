from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceSessionCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)


class WorkspaceSessionUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class WorkspaceMessageSendRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class WorkspaceMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: Literal["user", "assistant", "system"]
    content: str
    message_type: str
    metadata_json: dict
    created_at: datetime


class WorkspaceSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    message_count: int = 0
    last_message_preview: str | None = None
    created_at: datetime
    updated_at: datetime


class WorkspaceSessionDetailResponse(BaseModel):
    session: WorkspaceSessionResponse
    messages: list[WorkspaceMessageResponse]


class WorkspaceMessageSendResponse(BaseModel):
    session: WorkspaceSessionResponse
    user_message: WorkspaceMessageResponse
    assistant_message: WorkspaceMessageResponse


class RecentScoreItem(BaseModel):
    kind: Literal["resume_analysis", "interview_summary"]
    entity_id: UUID
    title: str
    score: float
    summary: str
    created_at: datetime
