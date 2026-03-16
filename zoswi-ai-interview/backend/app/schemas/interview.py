import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.interview import InterviewStatus, TranscriptSpeaker


class StartInterviewRequest(BaseModel):
    candidate_name: str = Field(min_length=2, max_length=200)
    role: str = Field(min_length=2, max_length=200)
    interview_type: str = Field(default="mixed", max_length=32)


class StartInterviewResponse(BaseModel):
    session_id: uuid.UUID
    websocket_path: str
    opening_question: str
    interview_type: str
    interview_duration_seconds: int
    max_turns: int


class EvaluationSignalsPayload(BaseModel):
    technical_accuracy: float
    communication_clarity: float
    confidence: float
    overall_rating: float
    summary_text: str


class TranscriptItem(BaseModel):
    speaker: TranscriptSpeaker
    text: str
    sequence_no: int
    created_at: datetime


class AIQuestionItem(BaseModel):
    id: uuid.UUID
    question_order: int
    question_text: str
    created_at: datetime


class CandidateResponseItem(BaseModel):
    id: uuid.UUID
    response_order: int
    transcript_text: str
    created_at: datetime


class InterviewResultResponse(BaseModel):
    session_id: uuid.UUID
    candidate_name: str
    role: str
    interview_type: str
    status: InterviewStatus
    turn_count: int
    max_turns: int
    current_question: str
    evaluation_signals: dict
    started_at: datetime
    ended_at: datetime | None
    transcripts: list[TranscriptItem]
    ai_questions: list[AIQuestionItem]
    candidate_responses: list[CandidateResponseItem]
    evaluation_summary: EvaluationSignalsPayload | None
