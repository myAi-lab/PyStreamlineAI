from fastapi import APIRouter, Depends

from app.api.deps import CurrentUserDep, DBSessionDep, enforce_rate_limit
from app.api.v1.responses import ok
from app.schemas.candidate import CandidateProfileResponse, CandidateProfileUpdateRequest
from app.schemas.common import SuccessResponse
from app.services.candidate_service import CandidateService

router = APIRouter(prefix="/candidate", tags=["candidate"])


@router.get("/profile", response_model=SuccessResponse[CandidateProfileResponse])
async def get_profile(
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    profile = await CandidateService(session).get_profile(current_user.id)
    return ok(profile.model_dump(mode="json"))


@router.put(
    "/profile",
    response_model=SuccessResponse[CandidateProfileResponse],
    dependencies=[Depends(enforce_rate_limit)],
)
async def update_profile(
    payload: CandidateProfileUpdateRequest,
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    profile = await CandidateService(session).update_profile(user_id=current_user.id, payload=payload)
    return ok(profile.model_dump(mode="json"))

