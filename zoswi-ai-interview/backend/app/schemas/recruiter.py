import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RecruiterCandidateItem(BaseModel):
    candidate_name: str
    role: str
    latest_session_id: uuid.UUID
    latest_overall_score: float | None = None
    status: str
    updated_at: datetime


class RecruiterInterviewItem(BaseModel):
    session_id: uuid.UUID
    candidate_name: str
    role: str
    interview_type: str
    status: str
    turn_count: int
    max_turns: int
    overall_score: float | None = None
    recommendation: str | None = None
    integrity_flag_count: int = 0
    created_at: datetime


class RecruiterReviewRequest(BaseModel):
    decision: str = Field(min_length=2, max_length=64)
    notes: str = Field(default="", max_length=5000)
    override_recommendation: bool = False


class RecruiterReviewResponse(BaseModel):
    review_id: uuid.UUID
    session_id: uuid.UUID
    reviewer_user_id: str
    decision: str
    notes: str
    override_recommendation: bool
    created_at: datetime


class RecruiterReplayResponse(BaseModel):
    session_id: uuid.UUID
    transcripts: list[dict]
    turns: list[dict]
    integrity_events: list[dict]


class RecruiterScorecardResponse(BaseModel):
    session_id: uuid.UUID
    final_assessment: dict
    turn_scores: list[dict]
    recruiter_reviews: list[dict]
