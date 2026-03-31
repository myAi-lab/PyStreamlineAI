from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import AIGateway
from app.ai.orchestrators.workspace_orchestrator import WorkspaceOrchestrator
from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError, NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.candidate_profile import CandidateProfile
from app.models.interview import InterviewSession, InterviewSummary
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.workspace import WorkspaceMessage, WorkspaceSession
from app.repositories.audit_repository import AuditRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.workspace import (
    RecentScoreItem,
    WorkspaceMessageResponse,
    WorkspaceMessageSendResponse,
    WorkspaceSessionCreateRequest,
    WorkspaceSessionDetailResponse,
    WorkspaceSessionResponse,
    WorkspaceSessionUpdateRequest,
)


class WorkspaceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.repo = WorkspaceRepository(session)
        self.audit_repo = AuditRepository(session)
        self.users = UserRepository(session)
        self.candidates = CandidateRepository(session)
        self.orchestrator = WorkspaceOrchestrator(AIGateway(self.settings))

    async def create_session(
        self,
        *,
        user_id: UUID,
        payload: WorkspaceSessionCreateRequest,
    ) -> WorkspaceSessionResponse:
        title = (payload.title or "").strip() or "New Chat"
        workspace_session = WorkspaceSession(user_id=user_id, title=title)
        await self.repo.create_session(workspace_session)

        welcome_message = WorkspaceMessage(
            session_id=workspace_session.id,
            role="assistant",
            content="Welcome to ZoSwi Live Workspace. Share your goal and I will help with a concrete plan.",
            message_type="text",
            metadata_json={},
        )
        await self.repo.create_message(welcome_message)
        await self.audit_repo.create(
            AuditLog(
                entity_type="workspace_session",
                entity_id=str(workspace_session.id),
                event_type="workspace_session_created",
                payload={"title": title},
            )
        )
        await self.session.commit()
        await self.session.refresh(workspace_session)
        return self._session_to_schema(workspace_session, message_count=1, last_message_preview=welcome_message.content)

    async def list_sessions(self, user_id: UUID) -> list[WorkspaceSessionResponse]:
        sessions = await self.repo.list_sessions_for_user(user_id)
        response: list[WorkspaceSessionResponse] = []
        for item in sessions:
            last_message = await self.repo.get_last_message(item.id)
            response.append(
                self._session_to_schema(
                    item,
                    message_count=await self.repo.count_messages(item.id),
                    last_message_preview=self._truncate_preview(last_message.content) if last_message else None,
                )
            )
        return response

    async def get_session_detail(self, *, user_id: UUID, session_id: UUID) -> WorkspaceSessionDetailResponse:
        workspace_session = await self.repo.get_session_for_user(user_id=user_id, session_id=session_id)
        if workspace_session is None:
            raise NotFoundError("Workspace session not found")
        messages = await self.repo.list_messages(session_id)
        session_response = self._session_to_schema(
            workspace_session,
            message_count=len(messages),
            last_message_preview=self._truncate_preview(messages[-1].content) if messages else None,
        )
        return WorkspaceSessionDetailResponse(
            session=session_response,
            messages=[WorkspaceMessageResponse.model_validate(msg) for msg in messages],
        )

    async def update_session(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        payload: WorkspaceSessionUpdateRequest,
    ) -> WorkspaceSessionResponse:
        workspace_session = await self.repo.get_session_for_user(user_id=user_id, session_id=session_id)
        if workspace_session is None:
            raise NotFoundError("Workspace session not found")
        workspace_session.title = payload.title.strip()
        await self.repo.touch_session(workspace_session)
        await self.audit_repo.create(
            AuditLog(
                entity_type="workspace_session",
                entity_id=str(workspace_session.id),
                event_type="workspace_session_renamed",
                payload={"title": workspace_session.title},
            )
        )
        await self.session.commit()
        await self.session.refresh(workspace_session)
        last_message = await self.repo.get_last_message(workspace_session.id)
        return self._session_to_schema(
            workspace_session,
            message_count=await self.repo.count_messages(workspace_session.id),
            last_message_preview=self._truncate_preview(last_message.content) if last_message else None,
        )

    async def send_message(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        message: str,
    ) -> WorkspaceMessageSendResponse:
        clean_message = message.strip()
        if not clean_message:
            raise ValidationError("Message cannot be empty")

        workspace_session = await self.repo.get_session_for_user(user_id=user_id, session_id=session_id)
        if workspace_session is None:
            raise NotFoundError("Workspace session not found")

        user_message = WorkspaceMessage(
            session_id=workspace_session.id,
            role="user",
            content=clean_message,
            message_type="text",
            metadata_json={},
        )
        await self.repo.create_message(user_message)
        await self.repo.touch_session(workspace_session)

        full_name = ""
        user = await self.users.get_by_id(user_id)
        if user is not None:
            full_name = user.full_name
        first_name = full_name.strip().split(" ")[0] if full_name.strip() else "Candidate"

        profile = await self.candidates.get_by_user_id(user_id)
        profile_context = self._format_profile(profile)
        existing_messages = await self.repo.list_messages(workspace_session.id, limit=20)
        conversation_summary = self._conversation_summary(existing_messages)

        try:
            ai_output = await self.orchestrator.generate_reply(
                candidate_name=first_name,
                profile_context=profile_context,
                conversation_summary=conversation_summary,
                user_message=clean_message,
            )
            assistant_text = self._build_assistant_content(
                primary_text=ai_output.response,
                key_points=ai_output.key_points,
                suggested_next_step=ai_output.suggested_next_step,
            )
            assistant_metadata = {
                "key_points": ai_output.key_points,
                "suggested_next_step": ai_output.suggested_next_step,
            }
        except ExternalServiceError:
            assistant_text = (
                "I hit a temporary AI response issue. Re-send your last message and I will continue from the same context."
            )
            assistant_metadata = {"fallback": True}

        assistant_message = WorkspaceMessage(
            session_id=workspace_session.id,
            role="assistant",
            content=assistant_text,
            message_type="text",
            metadata_json=assistant_metadata,
        )
        await self.repo.create_message(assistant_message)

        if workspace_session.title == "New Chat":
            workspace_session.title = self._title_from_user_message(clean_message)
        await self.repo.touch_session(workspace_session)

        await self.audit_repo.create(
            AuditLog(
                entity_type="workspace_session",
                entity_id=str(workspace_session.id),
                event_type="workspace_message_exchanged",
                payload={
                    "user_message_length": len(clean_message),
                    "assistant_message_length": len(assistant_text),
                },
            )
        )

        await self.session.commit()
        await self.session.refresh(workspace_session)
        await self.session.refresh(user_message)
        await self.session.refresh(assistant_message)

        message_count = await self.repo.count_messages(workspace_session.id)
        session_response = self._session_to_schema(
            workspace_session,
            message_count=message_count,
            last_message_preview=self._truncate_preview(assistant_message.content),
        )
        return WorkspaceMessageSendResponse(
            session=session_response,
            user_message=WorkspaceMessageResponse.model_validate(user_message),
            assistant_message=WorkspaceMessageResponse.model_validate(assistant_message),
        )

    async def list_recent_scores(self, *, user_id: UUID, limit: int = 25) -> list[RecentScoreItem]:
        resume_stmt: Select[tuple[ResumeAnalysis, Resume]] = (
            select(ResumeAnalysis, Resume)
            .join(Resume, Resume.id == ResumeAnalysis.resume_id)
            .where(Resume.user_id == user_id)
            .order_by(desc(ResumeAnalysis.created_at))
            .limit(limit)
        )
        interview_stmt: Select[tuple[InterviewSummary, InterviewSession]] = (
            select(InterviewSummary, InterviewSession)
            .join(InterviewSession, InterviewSession.id == InterviewSummary.session_id)
            .where(InterviewSession.user_id == user_id)
            .order_by(desc(InterviewSummary.created_at))
            .limit(limit)
        )
        resume_rows = (await self.session.execute(resume_stmt)).all()
        interview_rows = (await self.session.execute(interview_stmt)).all()

        items: list[RecentScoreItem] = []
        for analysis, resume in resume_rows:
            items.append(
                RecentScoreItem(
                    kind="resume_analysis",
                    entity_id=analysis.id,
                    title=resume.file_name or "Resume analysis",
                    score=self._derive_resume_score(analysis),
                    summary=analysis.summary,
                    created_at=analysis.created_at,
                )
            )

        for summary, session in interview_rows:
            scaled_score = summary.final_score * 10 if summary.final_score <= 10 else summary.final_score
            items.append(
                RecentScoreItem(
                    kind="interview_summary",
                    entity_id=summary.id,
                    title=f"{session.role_target} interview",
                    score=round(float(scaled_score), 2),
                    summary=summary.summary,
                    created_at=summary.created_at,
                )
            )

        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[:limit]

    @staticmethod
    def _title_from_user_message(message: str) -> str:
        words = [token.strip() for token in message.split() if token.strip()]
        if not words:
            return "New Chat"
        title = " ".join(words[:6])
        return title if len(words) <= 6 else f"{title}..."

    @staticmethod
    def _truncate_preview(content: str, limit: int = 140) -> str:
        text = content.replace("\n", " ").strip()
        if len(text) <= limit:
            return text
        return f"{text[:limit - 3]}..."

    @staticmethod
    def _session_to_schema(
        workspace_session: WorkspaceSession,
        *,
        message_count: int,
        last_message_preview: str | None,
    ) -> WorkspaceSessionResponse:
        return WorkspaceSessionResponse(
            id=workspace_session.id,
            user_id=workspace_session.user_id,
            title=workspace_session.title,
            message_count=message_count,
            last_message_preview=last_message_preview,
            created_at=workspace_session.created_at,
            updated_at=workspace_session.updated_at,
        )

    @staticmethod
    def _format_profile(profile: CandidateProfile | None) -> str:
        if profile is None:
            return "No profile available."
        target_roles = ", ".join(profile.target_roles) if profile.target_roles else "N/A"
        return (
            f"Headline: {profile.headline or 'N/A'}\n"
            f"Years Experience: {profile.years_experience if profile.years_experience is not None else 'N/A'}\n"
            f"Target Roles: {target_roles}\n"
            f"Location: {profile.location or 'N/A'}"
        )

    @classmethod
    def _conversation_summary(cls, messages: Iterable[WorkspaceMessage]) -> str:
        chunks: list[str] = []
        for item in list(messages)[-12:]:
            role = item.role.title()
            chunks.append(f"{role}: {cls._truncate_preview(item.content, 280)}")
        return "\n".join(chunks) if chunks else "No prior conversation."

    @classmethod
    def _build_assistant_content(
        cls,
        *,
        primary_text: str,
        key_points: list[str],
        suggested_next_step: str | None,
    ) -> str:
        body = primary_text.strip()
        if key_points:
            points = "\n".join(f"- {point}" for point in key_points[:4] if point.strip())
            if points:
                body = f"{body}\n\nKey points:\n{points}"
        if suggested_next_step and suggested_next_step.strip():
            body = f"{body}\n\nNext step: {suggested_next_step.strip()}"
        return body.strip()

    @staticmethod
    def _derive_resume_score(analysis: ResumeAnalysis) -> float:
        strengths = len(analysis.strengths or [])
        weaknesses = len(analysis.weaknesses or [])
        suggestions = len(analysis.suggestions or [])
        base = 65 + (strengths * 6) - (weaknesses * 4) - (suggestions * 1.5)
        return round(max(0.0, min(100.0, float(base))), 2)
