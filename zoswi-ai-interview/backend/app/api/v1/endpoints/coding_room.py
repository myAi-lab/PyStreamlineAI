from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUserDep, DBSessionDep, enforce_rate_limit
from app.api.v1.responses import ok
from app.models.enums import InterviewMode
from app.schemas.coding_room import (
    CodingEvaluationRequest,
    CodingEvaluationResponse,
    CodingHiddenCheckRequest,
    CodingHiddenCheckResponse,
    CodingRoomStagesResponse,
    CodingStarterCodeResponse,
)
from app.schemas.common import SuccessResponse
from app.services.coding_room_service import CodingRoomService

router = APIRouter(prefix="/coding-room", tags=["coding-room"])


@router.get("/stages", response_model=SuccessResponse[CodingRoomStagesResponse])
async def list_coding_stages(
    session: DBSessionDep,
    role_target: str = Query(default="Software Engineer", min_length=2, max_length=200),
    interview_mode: InterviewMode = Query(default=InterviewMode.MIXED),
):
    result = CodingRoomService(session).list_stages(role_target=role_target, interview_mode=interview_mode)
    return ok(result.model_dump(mode="json"))


@router.get("/stages/{stage_index}/starter-code", response_model=SuccessResponse[CodingStarterCodeResponse])
async def get_starter_code(
    session: DBSessionDep,
    stage_index: int,
    language: str = Query(default="python", max_length=40),
    role_target: str = Query(default="Software Engineer", min_length=2, max_length=200),
):
    result = CodingRoomService(session).starter_code(stage_index=stage_index, language=language, role_target=role_target)
    return ok(result.model_dump(mode="json"))


@router.post(
    "/stages/{stage_index}/hidden-check",
    response_model=SuccessResponse[CodingHiddenCheckResponse],
    dependencies=[Depends(enforce_rate_limit)],
)
async def hidden_check(
    stage_index: int,
    payload: CodingHiddenCheckRequest,
    current_user: CurrentUserDep,
    session: DBSessionDep,
    role_target: str = Query(default="Software Engineer", min_length=2, max_length=200),
    language: str = Query(default="python", max_length=40),
):
    result = await CodingRoomService(session).hidden_check(
        user_id=current_user.id,
        stage_index=stage_index,
        language=language,
        payload=payload,
        role_target=role_target,
    )
    return ok(result.model_dump(mode="json"))


@router.post(
    "/stages/{stage_index}/evaluate",
    response_model=SuccessResponse[CodingEvaluationResponse],
    dependencies=[Depends(enforce_rate_limit)],
)
async def evaluate_stage(
    stage_index: int,
    payload: CodingEvaluationRequest,
    current_user: CurrentUserDep,
    session: DBSessionDep,
    role_target: str = Query(default="Software Engineer", min_length=2, max_length=200),
    language: str = Query(default="python", max_length=40),
):
    result = await CodingRoomService(session).evaluate(
        user_id=current_user.id,
        stage_index=stage_index,
        language=language,
        payload=payload,
        role_target=role_target,
    )
    return ok(result.model_dump(mode="json"))
