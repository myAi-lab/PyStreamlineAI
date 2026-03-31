from functools import lru_cache
from typing import Annotated, Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "ZoSwi AI Platform"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    frontend_origin: AnyHttpUrl | str = "http://localhost:3000"
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["http://localhost:3000"])

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/zoswi"
    alembic_database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/zoswi"
    database_schema: str = "public"
    database_pool_size: int = 20
    database_max_overflow: int = 20
    database_echo: bool = False

    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = True

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 30
    refresh_token_exp_days: int = 7

    ai_provider: Literal["openai", "anthropic", "mock"] = "openai"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ai_default_model: str = "gpt-4.1-mini"
    ai_timeout_seconds: float = 30.0
    ai_max_retries: int = 2
    ai_allow_mock_provider: bool = True

    upload_max_size_bytes: int = 5_000_000
    allowed_upload_content_types: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
        ]
    )

    storage_backend: Literal["local", "s3"] = "local"
    local_storage_path: str = "storage/files"
    s3_bucket_name: str | None = None
    s3_region: str | None = None
    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_always_eager: bool = False

    rate_limit_requests_per_minute: int = 120
    interview_max_turns: int = 8
    live_interview_app_url: str = "http://localhost:3000/interview"
    interview_launch_secret: str | None = None
    interview_launch_ttl_seconds: int = 900
    interview_launch_issuer: str = "zoswi-web"
    interview_launch_audience: str = "zoswi-interview-launch"

    google_oauth_client_id: str | None = None
    google_oauth_client_secret: str | None = None
    google_oauth_redirect_uri: str = "http://localhost:8000/api/v1/auth/oauth/google/callback"

    linkedin_oauth_client_id: str | None = None
    linkedin_oauth_client_secret: str | None = None
    linkedin_oauth_redirect_uri: str = "http://localhost:8000/api/v1/auth/oauth/linkedin/callback"

    oauth_state_exp_minutes: int = 10
    oauth_bridge_exp_minutes: int = 5

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, list):
            return value
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    @field_validator("allowed_upload_content_types", mode="before")
    @classmethod
    def _parse_upload_content_types(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, list):
            return value
        return [content_type.strip() for content_type in value.split(",") if content_type.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
