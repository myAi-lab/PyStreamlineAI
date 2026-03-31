import asyncio
from concurrent.futures import Future
from threading import Thread
from uuid import UUID

import structlog

from app.db.session import SessionLocal
from app.repositories.interview_repository import InterviewRepository
from app.repositories.job_repository import JobRepository
from app.services.job_service import JobService
from app.services.resume_analysis_service import ResumeAnalysisService
from app.services.scoring_engine_service import ScoringEngineService
from app.storage.factory import build_storage_backend
from app.workers.celery_app import celery_app
from app.core.config import get_settings
from app.models.interview import InterviewSummary

logger = structlog.get_logger(__name__)


def _run_coro(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: Future = Future()

    def _runner() -> None:
        try:
            value = asyncio.run(coro)
            result.set_result(value)
        except Exception as exc:  # pragma: no cover
            result.set_exception(exc)

    thread = Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()
    return result.result()


@celery_app.task(name="process_resume_analysis_task")
def process_resume_analysis_task(resume_id: str, job_id: str) -> None:
    _run_coro(_process_resume_analysis(UUID(resume_id), UUID(job_id)))


async def _process_resume_analysis(resume_id: UUID, job_id: UUID) -> None:
    async with SessionLocal() as session:
        job_repo = JobRepository(session)
        job_service = JobService(session)
        job = await job_repo.get_by_id(job_id)
        if job is not None:
            await job_service.mark_running(job)

        service = ResumeAnalysisService(session, storage_backend=build_storage_backend(get_settings()))
        try:
            analysis = await service.run_analysis_for_resume(resume_id=resume_id)
            if job is not None:
                await job_service.mark_succeeded(
                    job,
                    result={"resume_id": str(resume_id), "analysis_id": str(analysis.id)},
                )
        except Exception as exc:
            logger.exception("resume_analysis_task_failed", error=str(exc), resume_id=str(resume_id))
            if job is not None:
                await job_service.mark_failed(job, str(exc))
            raise


@celery_app.task(name="generate_interview_summary_task")
def generate_interview_summary_task(session_id: str, job_id: str) -> None:
    _run_coro(_generate_interview_summary(UUID(session_id), UUID(job_id)))


async def _generate_interview_summary(session_id: UUID, job_id: UUID) -> None:
    async with SessionLocal() as session:
        job_repo = JobRepository(session)
        job_service = JobService(session)
        interview_repo = InterviewRepository(session)
        scoring_engine = ScoringEngineService()
        job = await job_repo.get_by_id(job_id)
        if job is not None:
            await job_service.mark_running(job)

        try:
            interview_session = await interview_repo.get_session(session_id)
            if interview_session is None:
                raise ValueError("Session not found")
            turns = await interview_repo.list_turns(session_id)
            summary = await scoring_engine.summarize_session(session=interview_session, turns=turns)
            await interview_repo.upsert_summary(
                InterviewSummary(
                    session_id=interview_session.id,
                    final_score=summary.final_score,
                    recommendation=summary.recommendation,
                    strengths=summary.strengths,
                    improvement_areas=summary.improvement_areas,
                    summary=summary.summary,
                )
            )
            await session.commit()
            if job is not None:
                await job_service.mark_succeeded(job, {"session_id": str(session_id)})
        except Exception as exc:
            logger.exception("interview_summary_task_failed", error=str(exc), session_id=str(session_id))
            if job is not None:
                await job_service.mark_failed(job, str(exc))
            raise
