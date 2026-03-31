from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RecruiterCandidateSummary(BaseModel):
    candidate_user_id: UUID
    candidate_name: str
    profile_headline: str | None
    target_roles: list[str]
    latest_resume_skills: list[str]
    resume_strengths: list[str]
    resume_risks: list[str]
    latest_interview_score: float | None
    latest_recommendation: str | None
    interview_strengths: list[str]
    interview_improvement_areas: list[str]
    generated_at: datetime

