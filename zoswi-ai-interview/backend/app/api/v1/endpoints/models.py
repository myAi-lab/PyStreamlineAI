from fastapi import APIRouter

from app.api.v1.responses import ok
from app.schemas.common import SuccessResponse
from app.schemas.model_config import ModelConfigResponse
from app.services.platform_service import PlatformService
from app.api.deps import DBSessionDep

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/config", response_model=SuccessResponse[ModelConfigResponse])
async def model_config(session: DBSessionDep):
    config = PlatformService(session).model_config()
    return ok(config.model_dump(mode="json"))

