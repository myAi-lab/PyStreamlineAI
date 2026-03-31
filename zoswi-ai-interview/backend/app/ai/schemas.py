from typing import Literal

from pydantic import BaseModel, Field


class ResumeAnalysisAIOutput(BaseModel):
    extracted_skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    summary: str


class InterviewQuestionAIOutput(BaseModel):
    interviewer_message: str = Field(min_length=5)
    tone: Literal["professional", "probing", "neutral"] = "professional"
    next_action: Literal["follow_up", "next_question", "deep_dive", "conclude"] = "next_question"


class TurnEvaluationAIOutput(BaseModel):
    score_overall: float = Field(ge=0.0, le=10.0)
    score_communication: float = Field(ge=0.0, le=10.0)
    score_technical: float = Field(ge=0.0, le=10.0)
    score_confidence: float = Field(ge=0.0, le=10.0)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    feedback: str


class FinalSummaryAIOutput(BaseModel):
    final_score: float = Field(ge=0.0, le=10.0)
    recommendation: str
    strengths: list[str] = Field(default_factory=list)
    improvement_areas: list[str] = Field(default_factory=list)
    summary: str


class WorkspaceReplyAIOutput(BaseModel):
    response: str = Field(min_length=1)
    key_points: list[str] = Field(default_factory=list)
    suggested_next_step: str | None = None
