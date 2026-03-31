import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from fastapi.responses import ORJSONResponse as DefaultJSONResponse
except Exception:  # pragma: no cover
    from fastapi.responses import JSONResponse as DefaultJSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.error_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.core.redis import close_redis, init_redis
from app.db.session import SessionLocal
from app.middleware.correlation_id import CorrelationIdMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.schemas.platform import HealthResponse, ReadyResponse
from app.services.platform_service import PlatformService
from app.websocket.interview_ws import interview_ws_endpoint

settings = get_settings()
configure_logging(settings)

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_redis()
    yield
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=DefaultJSONResponse,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

register_exception_handlers(app)

app.include_router(api_router, prefix=settings.api_v1_prefix)
app.add_api_websocket_route("/api/v1/ws/interviews/{session_id}", interview_ws_endpoint)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    async with SessionLocal() as session:
        return await PlatformService(session).health()


@app.get("/ready", response_model=ReadyResponse)
async def ready() -> ReadyResponse:
    async with SessionLocal() as session:
        return await PlatformService(session).readiness()


@app.get("/")
async def root() -> dict:
    return {
        "service": settings.app_name,
        "environment": settings.environment,
        "timestamp": datetime.now(UTC).isoformat(),
    }
