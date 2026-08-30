from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, dashboard, documents, search
from app.core.config import get_settings
from app.core.database import init_db
from app.core.exceptions import AppError, app_error_handler, http_error_handler, unhandled_error_handler
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    get_settings().ensure_data_dirs()
    init_db()
    logger.info("IntelliDocs API ready")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    settings.ensure_data_dirs()
    init_db()  # idempotent; also safe for TestClient usage that skips lifespan
    app = FastAPI(
        title="IntelliDocs API",
        description="RAG knowledge assistant for uploaded documents.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.include_router(documents.router)
    app.include_router(chat.router)
    app.include_router(search.router)
    app.include_router(dashboard.router)
    return app


app = create_app()
