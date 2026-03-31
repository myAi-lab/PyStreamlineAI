from fastapi import APIRouter, Depends

from app.api.deps import CurrentUserDep, DBSessionDep, enforce_rate_limit
from app.api.v1.responses import ok
from app.schemas.careers import CareersMatchRequest, CareersMatchResponse
from app.schemas.common import SuccessResponse
from app.services.careers_service import CareersService

router = APIRouter(prefix="/careers", tags=["careers"])


@router.post(
    "/match",
    response_model=SuccessResponse[CareersMatchResponse],
    dependencies=[Depends(enforce_rate_limit)],
)
async def match_careers(
    payload: CareersMatchRequest,
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    result = await CareersService(session).match_jobs(user_id=current_user.id, payload=payload)
    return ok(result.model_dump(mode="json"))

