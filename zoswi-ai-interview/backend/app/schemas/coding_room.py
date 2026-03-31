from pydantic import BaseModel, Field
from app.models.enums import InterviewMode


class CodingRoomStagesRequest(BaseModel):
    role_target: str = Field(default="Software Engineer", min_length=2, max_length=200)
    interview_mode: InterviewMode = InterviewMode.MIXED


class CodingRoomStage(BaseModel):
    stage_index: int = Field(ge=1, le=3)
    title: str
    skill_focus: str
    challenge: str
    difficulty: str
    time_limit_min: int
    requirements: list[str] = Field(default_factory=list)
    hint_starters: list[str] = Field(default_factory=list)


class CodingRoomStagesResponse(BaseModel):
    role_target: str
    interview_mode: InterviewMode
    stages: list[CodingRoomStage]


class CodingStarterCodeResponse(BaseModel):
    stage_index: int = Field(ge=1, le=3)
    language: str
    code: str


class CodingHiddenCheckRequest(BaseModel):
    language: str = Field(default="python", max_length=40)
    code: str = Field(default="", max_length=50_000)
    resume_context: str = Field(default="", max_length=10_000)
    job_description_context: str = Field(default="", max_length=10_000)


class CodingHiddenCheckResponse(BaseModel):
    ran: bool = True
    total: int
    passed: int
    failed_cases: list[str] = Field(default_factory=list)
    summary: str
    ready_for_evaluation: bool


class CodingEvaluationRequest(BaseModel):
    language: str = Field(default="python", max_length=40)
    code: str = Field(default="", max_length=50_000)
    resume_context: str = Field(default="", max_length=10_000)
    job_description_context: str = Field(default="", max_length=10_000)


class CodingEvaluationResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    verdict: str
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    next_step: str

