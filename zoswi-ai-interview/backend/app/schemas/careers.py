from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class CareersMatchRequest(BaseModel):
    role_query: str = Field(min_length=2, max_length=255)
    preferred_location: str = Field(default="", max_length=255)
    visa_status: str = Field(default="", max_length=120)
    sponsorship_required: bool = False
    selected_position_types: list[str] = Field(default_factory=list, max_length=6)
    posted_within_days: int = Field(default=0, ge=0, le=30)
    max_results: int = Field(default=8, ge=3, le=20)
    resume_id: UUID | None = None
    target_job_description: str = Field(default="", max_length=20_000)


class CareersTopCompanyLink(BaseModel):
    name: str
    url: str


class CareersMatchResult(BaseModel):
    external_id: str | None = None
    title: str
    company: str
    location: str
    posted_at: datetime | None = None
    overall_score: int
    resume_match_score: int
    role_relevance: int
    sponsorship_status: str
    sponsorship_confidence: int
    reason: str
    missing_points: list[str] = Field(default_factory=list)
    apply_url: str | None = None
    position_tags: list[str] = Field(default_factory=list)
    source_provider: str


class CareersMatchFilters(BaseModel):
    role_query: str
    preferred_location: str
    visa_status: str
    sponsorship_required: bool
    selected_position_types: list[str]
    posted_within_days: int
    max_results: int


class CareersMatchResponse(BaseModel):
    filters: CareersMatchFilters
    results: list[CareersMatchResult]
    trace: list[str] = Field(default_factory=list)
    info_message: str | None = None
    top_company_links: list[CareersTopCompanyLink] = Field(default_factory=list)

