from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import SearchRequest, SearchHit
from app.services.analysis_service import semantic_search

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=list[SearchHit])
def search(payload: SearchRequest, db: Session = Depends(get_db)):
    return semantic_search(db, payload.query, payload.document_ids, payload.top_k)
