import logging
import hashlib
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError, DocumentNotReadyError
from app.core.security import is_allowed_file, sanitize_filename
from app.models.document import Document, DocumentStatus
from app.rag.pipeline import delete_from_index, ingest_file

logger = logging.getLogger(__name__)


def validate_upload(filename: str, content_type: str | None, size: int) -> None:
    settings = get_settings()
    if size <= 0:
        raise AppError("The uploaded file is empty.", status_code=400, code="empty_file")
    if size > settings.max_upload_bytes:
        raise AppError(
            f"File is too large. Maximum size is {settings.max_upload_mb} MB.",
            status_code=413,
            code="file_too_large",
        )
    if not is_allowed_file(filename, content_type):
        raise AppError(
            "Unsupported file type. Upload PDF, DOCX, TXT, or Markdown.",
            status_code=415,
            code="unsupported_type",
        )


def create_document(
    db: Session,
    *,
    original_name: str,
    content_type: str,
    data: bytes,
) -> Document:
    validate_upload(original_name, content_type, len(data))
    safe_name = sanitize_filename(original_name)
    ext = Path(safe_name).suffix.lower()
    checksum = hashlib.sha256(data).hexdigest()
    doc = Document(
        filename=safe_name,
        original_filename=original_name,
        stored_path="",
        content_type=content_type or "application/octet-stream",
        file_ext=ext,
        size_bytes=len(data),
        status=DocumentStatus.pending.value,
        checksum=checksum,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    dest = get_settings().upload_path / f"{doc.id}{ext}"
    dest.write_bytes(data)
    doc.stored_path = str(dest)
    db.commit()
    db.refresh(doc)
    return doc


def process_document(db: Session, document_id: str) -> Document:
    doc = db.get(Document, document_id)
    if not doc:
        raise AppError("Document not found.", status_code=404, code="not_found")
    doc.status = DocumentStatus.processing.value
    doc.error_message = None
    db.commit()
    try:
        chunks, page_count = ingest_file(
            Path(doc.stored_path),
            document_id=doc.id,
            filename=doc.original_filename,
            file_ext=doc.file_ext,
        )
        doc.chunk_count = len(chunks)
        doc.page_count = page_count
        doc.status = DocumentStatus.ready.value
        db.commit()
        db.refresh(doc)
        return doc
    except Exception as exc:
        logger.exception("Document processing failed for %s", document_id)
        doc.status = DocumentStatus.failed.value
        doc.error_message = str(exc)
        db.commit()
        raise AppError(str(exc), status_code=422, code="processing_failed") from exc


def list_documents(db: Session) -> list[Document]:
    return list(db.scalars(select(Document).order_by(Document.created_at.desc())).all())


def get_document(db: Session, document_id: str) -> Document:
    doc = db.get(Document, document_id)
    if not doc:
        raise AppError("Document not found.", status_code=404, code="not_found")
    return doc


def require_ready(doc: Document) -> None:
    if doc.status != DocumentStatus.ready.value:
        raise DocumentNotReadyError(
            "This document is not ready yet. Wait until processing finishes."
            if doc.status != DocumentStatus.failed.value
            else f"Processing failed: {doc.error_message or 'unknown error'}"
        )


def delete_document(db: Session, document_id: str) -> None:
    doc = get_document(db, document_id)
    delete_from_index(document_id)
    path = Path(doc.stored_path) if doc.stored_path else None
    if path and path.exists():
        path.unlink()
    db.delete(doc)
    db.commit()


def count_documents(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Document)) or 0


def sum_chunks(db: Session) -> int:
    return db.scalar(select(func.coalesce(func.sum(Document.chunk_count), 0))) or 0
