from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.enums import UserRole
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.interview_repository import InterviewRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository
from app.schemas.recruiter import RecruiterCandidateSummary


class RecruiterReadinessService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.candidates = CandidateRepository(session)
        self.resumes = ResumeRepository(session)
        self.interviews = InterviewRepository(session)

    async def build_candidate_summary(
        self,
        *,
        requester_role: UserRole,
        requester_user_id: UUID,
        candidate_user_id: UUID,
    ) -> RecruiterCandidateSummary:
        if requester_role == UserRole.CANDIDATE and requester_user_id != candidate_user_id:
            raise NotFoundError("Candidate not found")

        user = await self.users.get_by_id(candidate_user_id)
        if user is None:
            raise NotFoundError("Candidate user not found")

        profile = await self.candidates.get_by_user_id(candidate_user_id)
        latest_resume_analysis = await self.resumes.get_latest_analysis_for_user(candidate_user_id)
        latest_summary = await self.interviews.get_latest_summary_for_user(candidate_user_id)

        return RecruiterCandidateSummary(
            candidate_user_id=user.id,
            candidate_name=user.full_name,
            profile_headline=profile.headline if profile else None,
            target_roles=profile.target_roles if profile else [],
            latest_resume_skills=latest_resume_analysis.extracted_skills if latest_resume_analysis else [],
            resume_strengths=latest_resume_analysis.strengths if latest_resume_analysis else [],
            resume_risks=latest_resume_analysis.weaknesses if latest_resume_analysis else [],
            latest_interview_score=latest_summary.final_score if latest_summary else None,
            latest_recommendation=latest_summary.recommendation if latest_summary else None,
            interview_strengths=latest_summary.strengths if latest_summary else [],
            interview_improvement_areas=latest_summary.improvement_areas if latest_summary else [],
            generated_at=datetime.now(UTC),
        )

