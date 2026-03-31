from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUserDep, DBSessionDep, RedisDep, enforce_rate_limit
from app.api.v1.responses import ok
from app.schemas.common import SuccessResponse
from app.schemas.interview import (
    InterviewRespondRequest,
    InterviewRespondResponse,
    InterviewMode,
    InterviewSessionCreateRequest,
    InterviewSessionDetailResponse,
    InterviewSessionResponse,
    InterviewStartResponse,
    InterviewSummaryResponse,
    LiveInterviewLaunchRequest,
    LiveInterviewLaunchResponse,
)
from app.services.live_interview_launch_service import LiveInterviewLaunchService
from app.services.interview_session_service import InterviewSessionService

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post(
    "/sessions",
    response_model=SuccessResponse[InterviewSessionResponse],
    dependencies=[Depends(enforce_rate_limit)],
)
async def create_session(
    payload: InterviewSessionCreateRequest,
    session: DBSessionDep,
    current_user: CurrentUserDep,
    redis_client: RedisDep,
):
    service = InterviewSessionService(session, redis_client=redis_client)
    created = await service.create_session(user_id=current_user.id, payload=payload)
    return ok(created.model_dump(mode="json"))


@router.get("/sessions", response_model=SuccessResponse[list[InterviewSessionResponse]])
async def list_sessions(
    session: DBSessionDep,
    current_user: CurrentUserDep,
    redis_client: RedisDep,
):
    service = InterviewSessionService(session, redis_client=redis_client)
    sessions = await service.list_sessions(current_user.id)
    return ok([item.model_dump(mode="json") for item in sessions])


@router.get("/sessions/{session_id}", response_model=SuccessResponse[InterviewSessionDetailResponse])
async def get_session(
    session_id: UUID,
    session: DBSessionDep,
    current_user: CurrentUserDep,
    redis_client: RedisDep,
):
    detail = await InterviewSessionService(session, redis_client=redis_client).get_session_detail(
        user_id=current_user.id,
        session_id=session_id,
    )
    return ok(detail.model_dump(mode="json"))


@router.post(
    "/sessions/{session_id}/start",
    response_model=SuccessResponse[InterviewStartResponse],
    dependencies=[Depends(enforce_rate_limit)],
)
async def start_session(
    session_id: UUID,
    session: DBSessionDep,
    current_user: CurrentUserDep,
    redis_client: RedisDep,
):
    started = await InterviewSessionService(session, redis_client=redis_client).start_session(
        user_id=current_user.id,
        session_id=session_id,
    )
    return ok(started.model_dump(mode="json"))


@router.post(
    "/sessions/{session_id}/respond",
    response_model=SuccessResponse[InterviewRespondResponse],
    dependencies=[Depends(enforce_rate_limit)],
)
async def respond(
    session_id: UUID,
    payload: InterviewRespondRequest,
    session: DBSessionDep,
    current_user: CurrentUserDep,
    redis_client: RedisDep,
):
    result = await InterviewSessionService(session, redis_client=redis_client).respond(
        user_id=current_user.id,
        session_id=session_id,
        answer=payload.answer,
    )
    return ok(result.model_dump(mode="json"))


@router.get(
    "/sessions/{session_id}/summary",
    response_model=SuccessResponse[InterviewSummaryResponse],
)
async def get_summary(
    session_id: UUID,
    session: DBSessionDep,
    current_user: CurrentUserDep,
    redis_client: RedisDep,
):
    summary = await InterviewSessionService(session, redis_client=redis_client).get_summary(
        user_id=current_user.id,
        session_id=session_id,
    )
    return ok(summary.model_dump(mode="json"))


@router.post(
    "/live/launch-url",
    response_model=SuccessResponse[LiveInterviewLaunchResponse],
    dependencies=[Depends(enforce_rate_limit)],
)
async def create_live_interview_launch_url(
    payload: LiveInterviewLaunchRequest,
    current_user: CurrentUserDep,
):
    normalized_payload = LiveInterviewLaunchRequest(
        candidate_name=payload.candidate_name.strip(),
        target_role=payload.target_role.strip(),
        requirement_type=InterviewMode(payload.requirement_type),
    )
    result = LiveInterviewLaunchService().build_launch_url(user=current_user, payload=normalized_payload)
    return ok(result.model_dump(mode="json"))
