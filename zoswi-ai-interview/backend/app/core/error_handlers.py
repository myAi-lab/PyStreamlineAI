from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog

from app.core.correlation import get_request_id
from app.core.exceptions import PlatformException

logger = structlog.get_logger(__name__)


def _error_payload(code: str, message: str, details: dict | None = None) -> dict:
    return {
        "success": False,
        "error": {"code": code, "message": message, "details": details or {}},
        "request_id": get_request_id(),
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PlatformException)
    async def platform_exception_handler(_: Request, exc: PlatformException) -> JSONResponse:
        logger.warning(
            "platform_exception",
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = {"errors": exc.errors()}
        logger.info("request_validation_error", details=details)
        return JSONResponse(
            status_code=422,
            content=_error_payload("request_validation_error", "Invalid request payload", details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        logger.info("http_exception", status_code=exc.status_code, detail=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload("http_error", str(exc.detail), {}),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content=_error_payload("internal_server_error", "Unexpected server error", {}),
        )

