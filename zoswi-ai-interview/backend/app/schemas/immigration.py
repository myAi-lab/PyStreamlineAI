from datetime import datetime
from pydantic import BaseModel, Field


class ImmigrationSearchRequest(BaseModel):
    query: str = Field(default="", max_length=200)
    visa_categories: list[str] = Field(default_factory=list, max_length=8)
    limit: int = Field(default=20, ge=1, le=50)
    force_refresh: bool = False


class ImmigrationUpdateResponse(BaseModel):
    id: str
    title: str
    summary: str
    source: str
    source_url: str | None = None
    link: str
    visa_category: str
    published_date: datetime | None = None
    tags: list[str] = Field(default_factory=list)


class ImmigrationSearchResponse(BaseModel):
    updates: list[ImmigrationUpdateResponse] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    live_note: str = ""
    last_refreshed_at: datetime | None = None


class ImmigrationRefreshResponse(BaseModel):
    refreshed: bool
    fetched_count: int
    message: str
    last_refreshed_at: datetime | None = None


class ImmigrationBriefRequest(BaseModel):
    query: str = Field(default="", max_length=200)
    visa_categories: list[str] = Field(default_factory=list, max_length=8)
    limit: int = Field(default=10, ge=3, le=20)


class ImmigrationBriefResponse(BaseModel):
    brief: str
    generated_at: datetime

