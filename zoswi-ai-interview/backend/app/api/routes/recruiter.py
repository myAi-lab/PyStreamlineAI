import csv
import io
import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_roles
from app.core.auth import AuthContext, UserRole
from app.core.exceptions import AppError
from app.core.rate_limit import enforce_recruiter_review_rate_limit
from app.models.interview import FinalAssessment, IntegrityEvent, InterviewSession
from app.repositories.interview_repository import InterviewRepository
from app.schemas.recruiter import (
    RecruiterCandidateItem,
    RecruiterInterviewItem,
    RecruiterReplayResponse,
    RecruiterReviewRequest,
    RecruiterReviewResponse,
    RecruiterScorecardResponse,
)

router = APIRouter(prefix="/recruiter", tags=["recruiter"])


@router.get("/candidates", response_model=list[RecruiterCandidateItem])
async def list_candidates(
    role: str = Query(default=""),
    min_score: float | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: AuthContext = Depends(require_roles(UserRole.recruiter, UserRole.admin)),
) -> list[RecruiterCandidateItem]:
    repository = InterviewRepository(db)
    sessions = await repository.list_sessions_for_recruiter(role_filter=role, min_score=min_score, limit=200)
    latest_by_candidate: dict[str, InterviewSession] = {}
    for session in sessions:
        candidate_key = str(session.candidate_name or "").strip().lower()
        current = latest_by_candidate.get(candidate_key)
        if current is None or session.updated_at > current.updated_at:
            latest_by_candidate[candidate_key] = session

    items: list[RecruiterCandidateItem] = []
    for session in latest_by_candidate.values():
        assessment_result = await db.execute(select(FinalAssessment).where(FinalAssessment.session_id == session.id))
        assessment = assessment_result.scalar_one_or_none()
        items.append(
            RecruiterCandidateItem(
                candidate_name=session.candidate_name,
                role=session.role,
                latest_session_id=session.id,
                latest_overall_score=(float(assessment.overall_score) if assessment else None),
                status=session.status.value,
                updated_at=session.updated_at,
            )
        )
    return sorted(items, key=lambda item: item.updated_at, reverse=True)


@router.get("/interviews", response_model=list[RecruiterInterviewItem])
async def list_interviews(
    role: str = Query(default=""),
    min_score: float | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: AuthContext = Depends(require_roles(UserRole.recruiter, UserRole.admin)),
) -> list[RecruiterInterviewItem]:
    repository = InterviewRepository(db)
    sessions = await repository.list_sessions_for_recruiter(role_filter=role, min_score=min_score, limit=250)
    rows: list[RecruiterInterviewItem] = []
    for session in sessions:
        assessment_result = await db.execute(select(FinalAssessment).where(FinalAssessment.session_id == session.id))
        assessment = assessment_result.scalar_one_or_none()
        integrity_result = await db.execute(
            select(func.count(IntegrityEvent.id)).where(IntegrityEvent.session_id == session.id)
        )
        integrity_count = int(integrity_result.scalar_one() or 0)
        rows.append(
            RecruiterInterviewItem(
                session_id=session.id,
                candidate_name=session.candidate_name,
                role=session.role,
                interview_type=session.interview_type,
                status=session.status.value,
                turn_count=session.turn_count,
                max_turns=session.max_turns,
                overall_score=(float(assessment.overall_score) if assessment else None),
                recommendation=(assessment.recommendation if assessment else None),
                integrity_flag_count=integrity_count,
                created_at=session.created_at,
            )
        )
    return rows


@router.get("/interviews/{session_id}")
async def get_interview(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: AuthContext = Depends(require_roles(UserRole.recruiter, UserRole.admin)),
) -> dict:
    repository = InterviewRepository(db)
    session = await repository.get_session_detail(session_id)
    if session is None:
        raise AppError(status_code=404, message="Interview session not found.")
    assessment_result = await db.execute(select(FinalAssessment).where(FinalAssessment.session_id == session.id))
    assessment = assessment_result.scalar_one_or_none()
    return {
        "session_id": str(session.id),
        "candidate_name": session.candidate_name,
        "role": session.role,
        "interview_type": session.interview_type,
        "status": session.status.value,
        "turn_count": session.turn_count,
        "max_turns": session.max_turns,
        "evaluation_signals": session.evaluation_signals,
        "final_assessment": {
            "overall_score": float(assessment.overall_score),
            "competency_coverage": float(assessment.competency_coverage),
            "recommendation": assessment.recommendation,
            "strengths": assessment.strengths,
            "weaknesses": assessment.weaknesses,
            "summary_text": assessment.summary_text,
        }
        if assessment
        else None,
    }


@router.get("/interviews/{session_id}/replay", response_model=RecruiterReplayResponse)
async def get_interview_replay(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: AuthContext = Depends(require_roles(UserRole.recruiter, UserRole.admin)),
) -> RecruiterReplayResponse:
    repository = InterviewRepository(db)
    session = await repository.get_session_detail(session_id)
    if session is None:
        raise AppError(status_code=404, message="Interview session not found.")
    turn_scores = await repository.list_turn_scores(session_id)
    integrity_events = await repository.list_integrity_events(session_id)
    return RecruiterReplayResponse(
        session_id=session_id,
        transcripts=[
            {
                "speaker": item.speaker.value,
                "text": item.message_text,
                "sequence_no": item.sequence_no,
                "created_at": item.created_at.isoformat(),
            }
            for item in sorted(session.transcripts, key=lambda row: row.sequence_no)
        ],
        turns=[
            {
                "turn_id": str(item.turn_id),
                "weighted_score": float(item.weighted_score),
                "evidence_snippet": item.evidence_snippet,
                "coverage_update": item.coverage_update,
            }
            for item in turn_scores
        ],
        integrity_events=[
            {
                "event_type": item.event_type,
                "severity": float(item.severity),
                "details": item.details,
                "created_at": item.created_at.isoformat(),
            }
            for item in integrity_events
        ],
    )


@router.get("/interviews/{session_id}/scorecard", response_model=RecruiterScorecardResponse)
async def get_interview_scorecard(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: AuthContext = Depends(require_roles(UserRole.recruiter, UserRole.admin)),
) -> RecruiterScorecardResponse:
    repository = InterviewRepository(db)
    session = await repository.get_session(session_id)
    if session is None:
        raise AppError(status_code=404, message="Interview session not found.")
    assessment_result = await db.execute(select(FinalAssessment).where(FinalAssessment.session_id == session.id))
    assessment = assessment_result.scalar_one_or_none()
    turns = await repository.list_turn_scores(session_id)
    reviews = await repository.list_recruiter_reviews(session_id)
    return RecruiterScorecardResponse(
        session_id=session_id,
        final_assessment={
            "overall_score": float(assessment.overall_score) if assessment else 0.0,
            "competency_coverage": float(assessment.competency_coverage) if assessment else 0.0,
            "recommendation": assessment.recommendation if assessment else "No Hire",
            "strengths": assessment.strengths if assessment else [],
            "weaknesses": assessment.weaknesses if assessment else [],
            "summary_text": assessment.summary_text if assessment else "",
        },
        turn_scores=[
            {
                "technical_correctness": float(item.technical_correctness),
                "problem_solving_debugging": float(item.problem_solving_debugging),
                "architecture_design": float(item.architecture_design),
                "communication_clarity": float(item.communication_clarity),
                "tradeoff_reasoning": float(item.tradeoff_reasoning),
                "professional_integrity": float(item.professional_integrity),
                "confidence_score": float(item.confidence_score),
                "weighted_score": float(item.weighted_score),
                "evidence_snippet": item.evidence_snippet,
                "coverage_update": item.coverage_update,
            }
            for item in turns
        ],
        recruiter_reviews=[
            {
                "review_id": str(item.id),
                "reviewer_user_id": item.reviewer_user_id,
                "decision": item.decision,
                "notes": item.notes,
                "override_recommendation": item.override_recommendation,
                "created_at": item.created_at.isoformat(),
            }
            for item in reviews
        ],
    )


@router.post("/interviews/{session_id}/review", response_model=RecruiterReviewResponse)
async def create_recruiter_review(
    session_id: uuid.UUID,
    payload: RecruiterReviewRequest,
    db: AsyncSession = Depends(get_db),
    auth_ctx: AuthContext = Depends(require_roles(UserRole.recruiter, UserRole.admin)),
) -> RecruiterReviewResponse:
    await enforce_recruiter_review_rate_limit(auth_ctx.user_id)
    repository = InterviewRepository(db)
    session = await repository.get_session(session_id)
    if session is None:
        raise AppError(status_code=404, message="Interview session not found.")

    review = await repository.add_recruiter_review(
        session_id=session_id,
        reviewer_user_id=auth_ctx.user_id,
        decision=payload.decision,
        notes=payload.notes,
        override_recommendation=payload.override_recommendation,
    )
    await repository.commit()
    return RecruiterReviewResponse(
        review_id=review.id,
        session_id=session_id,
        reviewer_user_id=review.reviewer_user_id,
        decision=review.decision,
        notes=review.notes,
        override_recommendation=review.override_recommendation,
        created_at=review.created_at,
    )


@router.get("/exports")
async def export_interviews(
    role: str = Query(default=""),
    min_score: float | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: AuthContext = Depends(require_roles(UserRole.recruiter, UserRole.admin)),
):
    repository = InterviewRepository(db)
    sessions = await repository.list_sessions_for_recruiter(role_filter=role, min_score=min_score, limit=500)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["session_id", "candidate_name", "role", "status", "overall_score", "recommendation", "created_at"])
    for session in sessions:
        assessment_result = await db.execute(select(FinalAssessment).where(FinalAssessment.session_id == session.id))
        assessment = assessment_result.scalar_one_or_none()
        writer.writerow(
            [
                str(session.id),
                session.candidate_name,
                session.role,
                session.status.value,
                float(assessment.overall_score) if assessment else "",
                assessment.recommendation if assessment else "",
                session.created_at.isoformat(),
            ]
        )
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=zoswi_interviews_export.csv"},
    )
