import logging
from pathlib import Path

from app.rag.chunking import chunk_pages
from app.rag.extraction import extract_text
from app.rag.types import Chunk
from app.vectorstore.factory import get_vector_store

logger = logging.getLogger(__name__)


def ingest_file(path: Path, *, document_id: str, filename: str, file_ext: str) -> tuple[list[Chunk], int]:
    pages = extract_text(path, file_ext)
    nonempty = [p for p in pages if (p.text or "").strip()]
    if not nonempty:
        raise ValueError("No text could be extracted. The file may be empty, scanned (image-only), or corrupted.")
    chunks = chunk_pages(nonempty, document_id=document_id, filename=filename)
    if not chunks:
        raise ValueError("The document produced no chunks after cleaning.")
    get_vector_store().upsert_chunks(chunks)
    page_count = max((p.page_number or 0) for p in pages)
    return chunks, page_count


def delete_from_index(document_id: str) -> None:
    get_vector_store().delete_document(document_id)
