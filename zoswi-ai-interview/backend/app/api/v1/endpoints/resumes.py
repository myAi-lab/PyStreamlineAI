from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.deps import CurrentUserDep, DBSessionDep, enforce_rate_limit
from app.api.v1.responses import ok
from app.core.config import get_settings
from app.schemas.common import SuccessResponse
from app.schemas.resume import (
    ResumeAnalysisResponse,
    ResumeAnalyzeTextRequest,
    ResumeDetailResponse,
    ResumeProcessResponse,
    ResumeResponse,
)
from app.services.resume_analysis_service import ResumeAnalysisService
from app.storage.factory import build_storage_backend

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post(
    "/upload",
    response_model=SuccessResponse[ResumeProcessResponse],
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(enforce_rate_limit)],
)
async def upload_resume(
    session: DBSessionDep,
    current_user: CurrentUserDep,
    file: UploadFile = File(...),
):
    service = ResumeAnalysisService(session, storage_backend=build_storage_backend(get_settings()))
    resume = await service.create_from_upload(user_id=current_user.id, upload=file)
    job_id = await service.queue_analysis(resume=resume)
    return ok(
        ResumeProcessResponse(
            resume=ResumeResponse.model_validate(resume),
            job_id=job_id,
            analysis=None,
        ).model_dump(mode="json")
    )


@router.post(
    "/analyze-text",
    response_model=SuccessResponse[ResumeProcessResponse],
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(enforce_rate_limit)],
)
async def analyze_resume_text(
    payload: ResumeAnalyzeTextRequest,
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    service = ResumeAnalysisService(session, storage_backend=build_storage_backend(get_settings()))
    resume = await service.create_from_text(
        user_id=current_user.id,
        raw_text=payload.raw_text,
        file_name=payload.file_name,
    )
    job_id = await service.queue_analysis(resume=resume)
    return ok(
        ResumeProcessResponse(
            resume=ResumeResponse.model_validate(resume),
            job_id=job_id,
            analysis=None,
        ).model_dump(mode="json")
    )


@router.get("", response_model=SuccessResponse[list[ResumeResponse]])
async def list_resumes(
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    service = ResumeAnalysisService(session, storage_backend=build_storage_backend(get_settings()))
    resumes = await service.list_resumes(user_id=current_user.id)
    return ok([resume.model_dump(mode="json") for resume in resumes])


@router.get("/{resume_id}", response_model=SuccessResponse[ResumeDetailResponse])
async def get_resume(
    resume_id: UUID,
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    service = ResumeAnalysisService(session, storage_backend=build_storage_backend(get_settings()))
    resume = await service.get_resume(user_id=current_user.id, resume_id=resume_id)
    return ok(ResumeDetailResponse.model_validate(resume).model_dump(mode="json"))


@router.get("/{resume_id}/analysis", response_model=SuccessResponse[ResumeAnalysisResponse])
async def get_resume_analysis(
    resume_id: UUID,
    session: DBSessionDep,
    current_user: CurrentUserDep,
):
    service = ResumeAnalysisService(session, storage_backend=build_storage_backend(get_settings()))
    analysis = await service.get_analysis_for_resume(user_id=current_user.id, resume_id=resume_id)
    return ok(analysis.model_dump(mode="json"))

