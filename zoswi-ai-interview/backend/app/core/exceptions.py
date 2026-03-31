from typing import Any


class PlatformException(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(PlatformException):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(code="auth_failed", message=message, status_code=401)


class AuthorizationError(PlatformException):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(code="forbidden", message=message, status_code=403)


class RateLimitError(PlatformException):
    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(code="rate_limit_exceeded", message=message, status_code=429)


class NotFoundError(PlatformException):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(code="not_found", message=message, status_code=404)


class ConflictError(PlatformException):
    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(code="conflict", message=message, status_code=409)


class ValidationError(PlatformException):
    def __init__(self, message: str = "Validation error", details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="validation_error",
            message=message,
            status_code=422,
            details=details,
        )


class ExternalServiceError(PlatformException):
    def __init__(self, message: str = "External service failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="external_service_error",
            message=message,
            status_code=502,
            details=details,
        )
