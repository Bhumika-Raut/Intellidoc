from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.exceptions import AppError
from app.schemas import (
    ActionItemsResponse,
    CompareRequest,
    CompareResponse,
    DocumentOut,
    InsightsResponse,
    SummaryResponse,
)
from app.services import analysis_service, document_service

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _process_in_background(document_id: str) -> None:
    db = SessionLocal()
    try:
        document_service.process_document(db, document_id)
    except AppError:
        pass
    finally:
        db.close()


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    data = await file.read()
    doc = document_service.create_document(
        db,
        original_name=file.filename or "upload.bin",
        content_type=file.content_type or "application/octet-stream",
        data=data,
    )
    background_tasks.add_task(_process_in_background, doc.id)
    return DocumentOut.model_validate(doc)


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return [DocumentOut.model_validate(d) for d in document_service.list_documents(db)]


@router.post("/compare", response_model=CompareResponse)
def compare(payload: CompareRequest, db: Session = Depends(get_db)):
    return analysis_service.compare_documents(db, payload.document_id_a, payload.document_id_b)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db)):
    return DocumentOut.model_validate(document_service.get_document(db, document_id))


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    document_service.delete_document(db, document_id)
    return None


@router.post("/{document_id}/process", response_model=DocumentOut)
def process_now(document_id: str, db: Session = Depends(get_db)):
    return DocumentOut.model_validate(document_service.process_document(db, document_id))


@router.post("/{document_id}/summarize", response_model=SummaryResponse)
def summarize(document_id: str, db: Session = Depends(get_db)):
    return analysis_service.summarize_document(db, document_id)


@router.post("/{document_id}/extract-insights", response_model=InsightsResponse)
def insights(document_id: str, db: Session = Depends(get_db)):
    return analysis_service.extract_insights(db, document_id)


@router.post("/{document_id}/action-items", response_model=ActionItemsResponse)
def action_items(document_id: str, db: Session = Depends(get_db)):
    return analysis_service.action_items(db, document_id)
