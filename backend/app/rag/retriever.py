from app.core.config import get_settings
from app.rag.types import Chunk
from app.schemas import Citation
from app.vectorstore.factory import get_vector_store

MIN_SCORE = 0.18


def retrieve(query: str, document_ids: list[str] | None = None, top_k: int | None = None) -> list[dict]:
    settings = get_settings()
    hits = get_vector_store().query(query, top_k=top_k or settings.retrieval_top_k, document_ids=document_ids)
    ranked = [h for h in hits if h.get("score") is None or h["score"] >= MIN_SCORE]
    return ranked or hits[:2]


def hits_to_citations(hits: list[dict]) -> list[Citation]:
    citations: list[Citation] = []
    for h in hits:
        excerpt = (h.get("text") or "").strip()
        if len(excerpt) > 420:
            excerpt = excerpt[:417] + "..."
        citations.append(
            Citation(
                document_id=h.get("document_id") or "",
                filename=h.get("filename") or "document",
                page=h.get("page"),
                section=h.get("section"),
                chunk_index=h.get("chunk_index"),
                excerpt=excerpt,
                score=h.get("score"),
            )
        )
    return citations


def document_context(document_id: str, query: str, top_k: int = 12) -> list[dict]:
    return retrieve(query, document_ids=[document_id], top_k=top_k)


def chunks_as_hits(chunks: list[Chunk]) -> list[dict]:
    return [
        {
            "text": c.text,
            "document_id": c.document_id,
            "filename": c.filename,
            "page": c.page_number,
            "section": c.section,
            "chunk_index": c.chunk_index,
            "score": None,
        }
        for c in chunks
    ]
