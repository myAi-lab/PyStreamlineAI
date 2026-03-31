from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InterviewMode, InterviewStatus


class InterviewSessionCreateRequest(BaseModel):
    role_target: str = Field(min_length=2, max_length=255)
    session_mode: InterviewMode = InterviewMode.MIXED


class InterviewSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    role_target: str
    status: InterviewStatus
    session_mode: InterviewMode
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime


class InterviewTurnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    turn_index: int
    interviewer_message: str
    candidate_message: str | None
    model_feedback: dict | None
    score_overall: float | None
    score_communication: float | None
    score_technical: float | None
    score_confidence: float | None
    created_at: datetime


class InterviewStartResponse(BaseModel):
    session: InterviewSessionResponse
    first_turn: InterviewTurnResponse
    is_complete: bool = False


class InterviewRespondRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=20_000)


class TurnEvaluationResponse(BaseModel):
    turn_id: UUID
    score_overall: float
    score_communication: float
    score_technical: float
    score_confidence: float
    strengths: list[str]
    weaknesses: list[str]
    feedback: str
    next_step_guidance: str


class InterviewRespondResponse(BaseModel):
    session: InterviewSessionResponse
    evaluated_turn: InterviewTurnResponse
    evaluation: TurnEvaluationResponse
    next_turn: InterviewTurnResponse | None = None
    is_complete: bool


class InterviewSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    final_score: float
    recommendation: str
    strengths: list[str]
    improvement_areas: list[str]
    summary: str
    created_at: datetime


class InterviewSessionDetailResponse(BaseModel):
    session: InterviewSessionResponse
    turns: list[InterviewTurnResponse]
    summary: InterviewSummaryResponse | None


class LiveInterviewLaunchRequest(BaseModel):
    candidate_name: str = Field(min_length=2, max_length=200)
    target_role: str = Field(min_length=2, max_length=200)
    requirement_type: InterviewMode = InterviewMode.MIXED


class LiveInterviewLaunchResponse(BaseModel):
    launch_url: str
    expires_at: datetime
