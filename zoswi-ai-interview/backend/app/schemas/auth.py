from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=200)
    role: UserRole = UserRole.CANDIDATE
    years_experience: float | None = Field(default=None, ge=0, le=50)
    role_contact_email: EmailStr | None = None
    profile_data: dict[str, str] = Field(default_factory=dict)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class OAuthExchangeRequest(BaseModel):
    bridge_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_token_expires_minutes: int


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role_contact_email: EmailStr | None = None
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AuthPayload(BaseModel):
    user: UserPublic
    tokens: TokenPair
