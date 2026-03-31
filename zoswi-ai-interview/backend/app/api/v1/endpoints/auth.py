from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse

from app.api.deps import CurrentUserDep, DBSessionDep, enforce_rate_limit
from app.api.v1.responses import ok
from app.core.config import get_settings
from app.schemas.auth import (
    AuthPayload,
    LoginRequest,
    OAuthExchangeRequest,
    RefreshTokenRequest,
    SignupRequest,
    TokenPair,
    UserPublic,
)
from app.schemas.common import SuccessResponse
from app.services.identity_service import IdentityService
from app.services.oauth_service import OAuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=SuccessResponse[AuthPayload],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit)],
)
async def signup(payload: SignupRequest, session: DBSessionDep):
    result = await IdentityService(session).signup(payload)
    return ok(result.model_dump(mode="json"))


@router.post(
    "/login",
    response_model=SuccessResponse[AuthPayload],
    dependencies=[Depends(enforce_rate_limit)],
)
async def login(payload: LoginRequest, session: DBSessionDep):
    result = await IdentityService(session).login(payload)
    return ok(result.model_dump(mode="json"))


@router.post(
    "/refresh",
    response_model=SuccessResponse[TokenPair],
    dependencies=[Depends(enforce_rate_limit)],
)
async def refresh(payload: RefreshTokenRequest, session: DBSessionDep):
    result = await IdentityService(session).refresh(payload.refresh_token)
    return ok(result.model_dump(mode="json"))


@router.get("/me", response_model=SuccessResponse[UserPublic])
async def me(current_user: CurrentUserDep):
    return ok(UserPublic.model_validate(current_user).model_dump(mode="json"))


@router.get("/oauth/{provider}/start", include_in_schema=True)
async def oauth_start(
    provider: Literal["google", "linkedin"],
    session: DBSessionDep,
):
    service = OAuthService(session)
    settings = get_settings()
    frontend_origin = str(settings.frontend_origin).rstrip("/")
    try:
        url = service.build_authorization_url(provider)
        return RedirectResponse(url=url, status_code=302)
    except Exception:
        return RedirectResponse(url=f"{frontend_origin}/login?oauth_error=1", status_code=302)


@router.get("/oauth/{provider}/callback", include_in_schema=True)
async def oauth_callback(
    provider: Literal["google", "linkedin"],
    session: DBSessionDep,
    code: str = Query(...),
    state: str = Query(...),
):
    service = OAuthService(session)
    settings = get_settings()
    frontend_origin = str(settings.frontend_origin).rstrip("/")

    try:
        bridge_token = await service.handle_callback(provider=provider, code=code, state=state)
        return RedirectResponse(
            url=f"{frontend_origin}/login/oauth/callback?bridge_token={bridge_token}",
            status_code=302,
        )
    except Exception:
        return RedirectResponse(url=f"{frontend_origin}/login?oauth_error=1", status_code=302)


@router.post(
    "/oauth/exchange",
    response_model=SuccessResponse[AuthPayload],
    dependencies=[Depends(enforce_rate_limit)],
)
async def oauth_exchange(payload: OAuthExchangeRequest, session: DBSessionDep):
    result = await OAuthService(session).exchange_bridge_token(payload.bridge_token)
    return ok(result.model_dump(mode="json"))
