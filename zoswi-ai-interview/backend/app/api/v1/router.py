from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    candidate,
    careers,
    coding_room,
    immigration,
    interviews,
    models,
    platform,
    recruiter,
    resumes,
    workspace,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(candidate.router)
api_router.include_router(resumes.router)
api_router.include_router(interviews.router)
api_router.include_router(careers.router)
api_router.include_router(coding_room.router)
api_router.include_router(immigration.router)
api_router.include_router(recruiter.router)
api_router.include_router(models.router)
api_router.include_router(platform.router)
api_router.include_router(workspace.router)
