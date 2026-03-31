from fastapi import APIRouter, Depends

from app.api.deps import CurrentUserDep, DBSessionDep, enforce_rate_limit
from app.api.v1.responses import ok
from app.schemas.common import SuccessResponse
from app.schemas.platform import FeedbackRequest, UsageResponse
from app.services.platform_service import PlatformService

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/me/usage", response_model=SuccessResponse[UsageResponse])
async def my_usage(session: DBSessionDep, current_user: CurrentUserDep):
    usage = await PlatformService(session).usage_for_user(current_user.id)
    return ok(usage.model_dump(mode="json"))


@router.post(
    "/feedback",
    response_model=SuccessResponse[dict],
    dependencies=[Depends(enforce_rate_limit)],
)
async def submit_feedback(
    payload: FeedbackRequest,
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    await PlatformService(session).submit_feedback(user_id=current_user.id, payload=payload)
    return ok({"accepted": True})

