from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "app_error"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class DocumentNotReadyError(AppError):
    def __init__(self, message: str = "Document is still processing."):
        super().__init__(message, status_code=409, code="document_not_ready")


class RetrievalError(AppError):
    def __init__(self, message: str = "Could not search the knowledge base."):
        super().__init__(message, status_code=503, code="retrieval_error")


class LLMError(AppError):
    def __init__(self, message: str = "The language model request failed."):
        super().__init__(message, status_code=502, code="llm_error")


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )


async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "Request could not be processed."
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


async def unhandled_error_handler(_: Request, __: Exception) -> JSONResponse:
    # Do not leak stack traces or internal paths to clients.
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again.", "code": "internal_error"},
    )
