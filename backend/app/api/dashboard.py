from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas import DashboardStats
from app.services.dashboard_service import get_dashboard

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db)):
    return get_dashboard(db)


@router.get("/health")
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "llm_provider": settings.llm_provider,
        "embedding_provider": settings.embedding_provider,
    }


@router.get("/settings/public")
def public_settings():
    settings = get_settings()
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.embedding_model,
        "max_upload_mb": settings.max_upload_mb,
        "retrieval_top_k": settings.retrieval_top_k,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        # Never include API keys.
    }
