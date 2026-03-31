from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUserDep, DBSessionDep, enforce_rate_limit
from app.api.v1.responses import ok
from app.schemas.common import SuccessResponse
from app.schemas.workspace import (
    RecentScoreItem,
    WorkspaceMessageSendRequest,
    WorkspaceMessageSendResponse,
    WorkspaceSessionCreateRequest,
    WorkspaceSessionDetailResponse,
    WorkspaceSessionResponse,
    WorkspaceSessionUpdateRequest,
)
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.post(
    "/sessions",
    response_model=SuccessResponse[WorkspaceSessionResponse],
    dependencies=[Depends(enforce_rate_limit)],
)
async def create_workspace_session(
    payload: WorkspaceSessionCreateRequest,
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    created = await WorkspaceService(session).create_session(user_id=current_user.id, payload=payload)
    return ok(created.model_dump(mode="json"))


@router.get("/sessions", response_model=SuccessResponse[list[WorkspaceSessionResponse]])
async def list_workspace_sessions(
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    sessions = await WorkspaceService(session).list_sessions(current_user.id)
    return ok([item.model_dump(mode="json") for item in sessions])


@router.get("/sessions/{session_id}", response_model=SuccessResponse[WorkspaceSessionDetailResponse])
async def get_workspace_session(
    session_id: UUID,
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    detail = await WorkspaceService(session).get_session_detail(user_id=current_user.id, session_id=session_id)
    return ok(detail.model_dump(mode="json"))


@router.patch(
    "/sessions/{session_id}",
    response_model=SuccessResponse[WorkspaceSessionResponse],
    dependencies=[Depends(enforce_rate_limit)],
)
async def update_workspace_session(
    session_id: UUID,
    payload: WorkspaceSessionUpdateRequest,
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    updated = await WorkspaceService(session).update_session(
        user_id=current_user.id,
        session_id=session_id,
        payload=payload,
    )
    return ok(updated.model_dump(mode="json"))


@router.post(
    "/sessions/{session_id}/messages",
    response_model=SuccessResponse[WorkspaceMessageSendResponse],
    dependencies=[Depends(enforce_rate_limit)],
)
async def send_workspace_message(
    session_id: UUID,
    payload: WorkspaceMessageSendRequest,
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    result = await WorkspaceService(session).send_message(
        user_id=current_user.id,
        session_id=session_id,
        message=payload.message,
    )
    return ok(result.model_dump(mode="json"))


@router.get("/recent-scores", response_model=SuccessResponse[list[RecentScoreItem]])
async def list_recent_scores(
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    scores = await WorkspaceService(session).list_recent_scores(user_id=current_user.id)
    return ok([item.model_dump(mode="json") for item in scores])
