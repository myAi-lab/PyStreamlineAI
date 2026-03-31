from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUserDep, DBSessionDep
from app.api.v1.responses import ok
from app.schemas.common import SuccessResponse
from app.schemas.recruiter import RecruiterCandidateSummary
from app.services.recruiter_readiness_service import RecruiterReadinessService

router = APIRouter(prefix="/recruiter", tags=["recruiter"])


@router.get("/readiness/{candidate_user_id}", response_model=SuccessResponse[RecruiterCandidateSummary])
async def candidate_readiness(
    candidate_user_id: UUID,
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    summary = await RecruiterReadinessService(session).build_candidate_summary(
        requester_role=current_user.role,
        requester_user_id=current_user.id,
        candidate_user_id=candidate_user_id,
    )
    return ok(summary.model_dump(mode="json"))

