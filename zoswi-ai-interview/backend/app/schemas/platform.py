from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime


class ReadyResponse(BaseModel):
    status: str
    checks: dict[str, str]
    timestamp: datetime


class UsageResponse(BaseModel):
    total_resumes: int
    total_resume_analyses: int
    total_sessions: int
    completed_sessions: int


class FeedbackRequest(BaseModel):
    category: str = Field(min_length=2, max_length=100)
    message: str = Field(min_length=5, max_length=5000)

