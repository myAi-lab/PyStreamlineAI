from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ResumeParseStatus, ResumeSourceType


class ResumeAnalyzeTextRequest(BaseModel):
    raw_text: str = Field(min_length=80, max_length=100_000)
    file_name: str | None = Field(default=None, max_length=255)


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    source_type: ResumeSourceType
    file_name: str | None
    storage_key: str | None
    parse_status: ResumeParseStatus
    created_at: datetime
    updated_at: datetime


class ResumeDetailResponse(ResumeResponse):
    raw_text: str


class ResumeAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resume_id: UUID
    extracted_skills: list[str]
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    summary: str
    model_name: str
    analysis_version: str
    created_at: datetime


class ResumeProcessResponse(BaseModel):
    resume: ResumeResponse
    job_id: UUID | None = None
    analysis: ResumeAnalysisResponse | None = None

