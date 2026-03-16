import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.interview import router as interview_router
from app.core.config import get_settings
from app.core.db import init_db
from app.core.exceptions import AppError, app_error_handler
from app.core.logging import configure_logging

settings = get_settings()
request_logger = logging.getLogger("app.requests")

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)
    await init_db()
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_exception_handler(AppError, app_error_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview_router)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    started = perf_counter()
    response = await call_next(request)
    duration_ms = round((perf_counter() - started) * 1000, 2)
    request_logger.info("%s %s -> %s (%sms)", request.method, request.url.path, response.status_code, duration_ms)
    return response


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
