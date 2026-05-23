from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.observability import get_logger
from app.observability.middleware import current_request_id

log = get_logger("app.errors")


def _envelope(status_code: int, code: str, message: str, *, details: object | None = None) -> JSONResponse:
    body: dict[str, object] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": current_request_id(),
        }
    }
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _envelope(exc.status_code, "http_error", str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _envelope(422, "validation_error", "Request validation failed", details=exc.errors())

    @app.exception_handler(ValueError)
    async def value_error(_: Request, exc: ValueError) -> JSONResponse:
        return _envelope(400, "invalid_request", str(exc))

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_exception", extra={"error_type": exc.__class__.__name__})
        return _envelope(500, "internal_error", "An internal error occurred")
