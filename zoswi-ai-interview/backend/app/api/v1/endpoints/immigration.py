from fastapi import APIRouter, Depends

from app.api.deps import CurrentUserDep, DBSessionDep, enforce_rate_limit
from app.api.v1.responses import ok
from app.schemas.common import SuccessResponse
from app.schemas.immigration import (
    ImmigrationBriefRequest,
    ImmigrationBriefResponse,
    ImmigrationRefreshResponse,
    ImmigrationSearchRequest,
    ImmigrationSearchResponse,
)
from app.services.immigration_service import ImmigrationService

router = APIRouter(prefix="/immigration", tags=["immigration"])


@router.post(
    "/search",
    response_model=SuccessResponse[ImmigrationSearchResponse],
    dependencies=[Depends(enforce_rate_limit)],
)
async def search_immigration_updates(
    payload: ImmigrationSearchRequest,
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    result = await ImmigrationService(session).search(user_id=current_user.id, payload=payload)
    return ok(result.model_dump(mode="json"))


@router.post(
    "/refresh",
    response_model=SuccessResponse[ImmigrationRefreshResponse],
    dependencies=[Depends(enforce_rate_limit)],
)
async def refresh_immigration_updates(
    session: DBSessionDep,
):
    result = await ImmigrationService(session).refresh(force=True)
    return ok(result.model_dump(mode="json"))


@router.post(
    "/brief",
    response_model=SuccessResponse[ImmigrationBriefResponse],
    dependencies=[Depends(enforce_rate_limit)],
)
async def build_immigration_brief(
    payload: ImmigrationBriefRequest,
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    result = await ImmigrationService(session).build_brief(user_id=current_user.id, payload=payload)
    return ok(result.model_dump(mode="json"))

