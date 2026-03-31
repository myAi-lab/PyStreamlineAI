from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CandidateProfileUpdateRequest(BaseModel):
    headline: str | None = Field(default=None, max_length=255)
    years_experience: float | None = Field(default=None, ge=0, le=50)
    target_roles: list[str] = Field(default_factory=list)
    location: str | None = Field(default=None, max_length=255)
    role_contact_email: EmailStr | None = None
    role_profile: dict[str, str] = Field(default_factory=dict)


class CandidateProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    headline: str | None
    years_experience: float | None
    target_roles: list[str]
    location: str | None
    role_contact_email: EmailStr | None
    role_profile: dict[str, str]
    created_at: datetime
    updated_at: datetime
