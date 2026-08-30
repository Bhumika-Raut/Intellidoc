from app.core.config import get_settings
from app.rag.cleaning import clean_text
from app.rag.types import Chunk, ExtractedPage


def chunk_pages(
    pages: list[ExtractedPage],
    *,
    document_id: str,
    filename: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    settings = get_settings()
    size = chunk_size or settings.chunk_size
    ov = overlap or settings.chunk_overlap
    chunks: list[Chunk] = []
    index = 0

    for page in pages:
        text = clean_text(page.text)
        if not text:
            continue
        pieces = _split_with_overlap(text, size, ov)
        for piece in pieces:
            chunks.append(
                Chunk(
                    text=piece,
                    chunk_index=index,
                    page_number=page.page_number,
                    section=page.section,
                    document_id=document_id,
                    filename=filename,
                )
            )
            index += 1
    return chunks


def _split_with_overlap(text: str, size: int, overlap: int) -> list[str]:
    if len(text) <= size:
        return [text]

    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            window = text[start:end]
            break_at = max(window.rfind("\n\n"), window.rfind(". "), window.rfind("\n"))
            if break_at > size * 0.4:
                end = start + break_at + 1
        piece = text[start:end].strip()
        if piece:
            parts.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return parts
