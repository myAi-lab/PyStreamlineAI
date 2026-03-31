from io import BytesIO
from uuid import UUID

from docx import Document
from fastapi import UploadFile
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import AIGateway
from app.ai.orchestrators.resume_orchestrator import ResumeOrchestrator
from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.enums import JobType, ResumeParseStatus, ResumeSourceType
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.repositories.audit_repository import AuditRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume import ResumeAnalysisResponse, ResumeResponse
from app.storage.base import StorageBackend


class ResumeAnalysisService:
    def __init__(self, session: AsyncSession, storage_backend: StorageBackend) -> None:
        self.session = session
        self.settings = get_settings()
        self.repo = ResumeRepository(session)
        self.audit_repo = AuditRepository(session)
        self.storage = storage_backend
        self.orchestrator = ResumeOrchestrator(AIGateway(self.settings))

    async def create_from_text(self, *, user_id: UUID, raw_text: str, file_name: str | None = None) -> Resume:
        resume = Resume(
            user_id=user_id,
            source_type=ResumeSourceType.PASTED_TEXT,
            file_name=file_name,
            raw_text=raw_text,
            parse_status=ResumeParseStatus.PROCESSING,
        )
        await self.repo.create(resume)
        await self.session.commit()
        await self.session.refresh(resume)
        return resume

    async def create_from_upload(self, *, user_id: UUID, upload: UploadFile) -> Resume:
        if upload.content_type not in self.settings.allowed_upload_content_types:
            raise ValidationError("Unsupported file type")

        content = await upload.read()
        if len(content) > self.settings.upload_max_size_bytes:
            raise ValidationError("Uploaded resume exceeds max size limit")

        raw_text = self._extract_text(content=content, content_type=upload.content_type or "")
        storage_key = await self.storage.save_file(
            file_name=upload.filename or "resume.bin",
            content=content,
            content_type=upload.content_type or "application/octet-stream",
        )
        resume = Resume(
            user_id=user_id,
            source_type=ResumeSourceType.UPLOAD,
            file_name=upload.filename,
            raw_text=raw_text,
            storage_key=storage_key,
            parse_status=ResumeParseStatus.PROCESSING,
        )
        await self.repo.create(resume)
        await self.session.commit()
        await self.session.refresh(resume)
        return resume

    def _extract_text(self, *, content: bytes, content_type: str) -> str:
        if content_type == "text/plain":
            return content.decode("utf-8", errors="ignore")

        if content_type == "application/pdf":
            reader = PdfReader(BytesIO(content))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)

        if content_type in {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        }:
            doc = Document(BytesIO(content))
            return "\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())

        return content.decode("utf-8", errors="ignore")

    async def queue_analysis(self, *, resume: Resume) -> UUID:
        from app.services.job_service import JobService
        from app.workers.tasks import process_resume_analysis_task

        job_service = JobService(self.session)
        job = await job_service.create_job(
            job_type=JobType.RESUME_ANALYSIS,
            payload={"resume_id": str(resume.id)},
            user_id=resume.user_id,
        )
        process_resume_analysis_task.delay(str(resume.id), str(job.id))
        return job.id

    async def run_analysis_for_resume(self, *, resume_id: UUID) -> ResumeAnalysis:
        resume = await self.repo.get_by_id(resume_id)
        if resume is None:
            raise NotFoundError("Resume not found")

        ai_output = await self.orchestrator.analyze_resume(resume.raw_text)
        resume.parse_status = ResumeParseStatus.COMPLETED
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            extracted_skills=ai_output.extracted_skills,
            strengths=ai_output.strengths,
            weaknesses=ai_output.weaknesses,
            suggestions=ai_output.suggestions,
            summary=ai_output.summary,
            model_name=self.settings.ai_default_model,
            analysis_version="v1",
        )
        persisted = await self.repo.upsert_analysis(analysis)
        await self.audit_repo.create(
            AuditLog(
                entity_type="resume",
                entity_id=str(resume.id),
                event_type="resume_analysis_completed",
                payload={"resume_id": str(resume.id), "model": self.settings.ai_default_model},
            )
        )
        await self.session.commit()
        await self.session.refresh(persisted)
        return persisted

    async def list_resumes(self, *, user_id: UUID) -> list[ResumeResponse]:
        resumes = await self.repo.list_for_user(user_id)
        return [ResumeResponse.model_validate(item) for item in resumes]

    async def get_resume(self, *, user_id: UUID, resume_id: UUID) -> Resume:
        resume = await self.repo.get_for_user(user_id=user_id, resume_id=resume_id)
        if resume is None:
            raise NotFoundError("Resume not found")
        return resume

    async def get_analysis_for_resume(self, *, user_id: UUID, resume_id: UUID) -> ResumeAnalysisResponse:
        resume = await self.get_resume(user_id=user_id, resume_id=resume_id)
        analysis = await self.repo.get_analysis(resume.id)
        if analysis is None:
            raise NotFoundError("Resume analysis not available yet")
        return ResumeAnalysisResponse.model_validate(analysis)

