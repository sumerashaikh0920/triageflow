"""Custom exceptions and FastAPI exception handlers for frontend-friendly errors."""
from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application error. Produces a consistent JSON error shape for the frontend."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, code: str = "app_error"):
        self.message = message
        self.status_code = status_code
        self.code = code


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND, "not_found")


class ForbiddenError(AppError):
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(message, status.HTTP_403_FORBIDDEN, "forbidden")


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Invalid or expired credentials"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, "unauthorized")


class ConflictError(AppError):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status.HTTP_409_CONFLICT, "conflict")


async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
