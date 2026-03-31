from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis import redis_client
from app.models.audit_log import AuditLog
from app.models.enums import InterviewStatus
from app.models.interview import InterviewSession
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.schemas.model_config import ModelConfigResponse
from app.schemas.platform import FeedbackRequest, HealthResponse, ReadyResponse, UsageResponse


class PlatformService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()

    async def health(self) -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=self.settings.app_name,
            timestamp=datetime.now(UTC),
        )

    async def readiness(self) -> ReadyResponse:
        checks = {"database": "unknown", "redis": "unknown"}
        try:
            await self.session.execute(select(1))
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "failed"

        if redis_client is None:
            checks["redis"] = "disabled"
        else:
            try:
                await redis_client.ping()
                checks["redis"] = "ok"
            except Exception:
                checks["redis"] = "failed"

        status = "ok" if all(value in {"ok", "disabled"} for value in checks.values()) else "degraded"
        return ReadyResponse(status=status, checks=checks, timestamp=datetime.now(UTC))

    async def usage_for_user(self, user_id: UUID) -> UsageResponse:
        total_resumes = await self.session.scalar(select(func.count(Resume.id)).where(Resume.user_id == user_id))
        total_resume_analyses = await self.session.scalar(
            select(func.count(ResumeAnalysis.id)).join(Resume, Resume.id == ResumeAnalysis.resume_id).where(
                Resume.user_id == user_id
            )
        )
        total_sessions = await self.session.scalar(
            select(func.count(InterviewSession.id)).where(InterviewSession.user_id == user_id)
        )
        completed_sessions = await self.session.scalar(
            select(func.count(InterviewSession.id)).where(
                InterviewSession.user_id == user_id,
                InterviewSession.status == InterviewStatus.COMPLETED,
            )
        )
        return UsageResponse(
            total_resumes=int(total_resumes or 0),
            total_resume_analyses=int(total_resume_analyses or 0),
            total_sessions=int(total_sessions or 0),
            completed_sessions=int(completed_sessions or 0),
        )

    async def submit_feedback(self, *, user_id: UUID, payload: FeedbackRequest) -> None:
        self.session.add(
            AuditLog(
                entity_type="platform_feedback",
                entity_id=str(user_id),
                event_type="feedback_submitted",
                payload={"category": payload.category, "message": payload.message},
            )
        )
        await self.session.commit()

    def model_config(self) -> ModelConfigResponse:
        return ModelConfigResponse(
            provider=self.settings.ai_provider,
            default_model=self.settings.ai_default_model,
            max_retries=self.settings.ai_max_retries,
            timeout_seconds=self.settings.ai_timeout_seconds,
            interview_max_turns=self.settings.interview_max_turns,
        )
