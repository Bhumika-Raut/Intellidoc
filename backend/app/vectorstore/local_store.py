import json
import logging
import math
import threading
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import RetrievalError
from app.embeddings.factory import get_embedding_provider
from app.rag.types import Chunk
from app.vectorstore.base import VectorStore

logger = logging.getLogger(__name__)


def _cosine(a: list[float], b: list[float], norm_b: float | None = None) -> float:
    dot = 0.0
    norm_a = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
    norm_a = math.sqrt(norm_a) or 1.0
    norm_b = norm_b if norm_b is not None else math.sqrt(sum(v * v for v in b)) or 1.0
    return dot / (norm_a * norm_b)


class LocalVectorStore(VectorStore):
    """Dependency-free persistent vector store (JSON on disk, cosine similarity).

    Default backend for IntelliDocs: no external service, no heavy transitive
    dependencies, survives restarts. Same interface as the optional ChromaDB
    backend, so switching via VECTOR_STORE=chroma requires no other changes.
    Suitable for demo/portfolio scale (hundreds to a few thousand chunks).
    """

    def __init__(self, path: Path | None = None, provider=None):
        settings = get_settings()
        self._path = Path(path) if path else settings.vector_dir / "chunks.json"
        self._provider = provider or get_embedding_provider()
        self._lock = threading.Lock()
        self._records: dict[str, dict[str, Any]] = {}
        self._load()

    # --- persistence -------------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            records = data.get("records", [])
            if isinstance(records, list):
                for rec in records:
                    if isinstance(rec, dict) and rec.get("id"):
                        self._records[str(rec["id"])] = rec
            logger.info("Loaded %d vectors from %s", len(self._records), self._path)
        except Exception:
            logger.warning("Could not read vector store file %s; starting with an empty store.", self._path)
            self._records = {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"records": list(self._records.values())})
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(self._path)  # atomic on the same volume

    # --- VectorStore API ---------------------------------------------------

    def upsert_chunks(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        ids = [f"{c.document_id}:{c.chunk_index}" for c in chunks]
        documents = [c.text for c in chunks]
        try:
            vectors = self._provider.embed_documents(documents)
        except Exception as exc:
            logger.exception("Embedding generation failed")
            raise RetrievalError("Failed to generate embeddings for this document.") from exc

        with self._lock:
            for chunk, vec, chunk_id in zip(chunks, vectors, ids):
                self._records[chunk_id] = {
                    "id": chunk_id,
                    "text": chunk.text,
                    "vector": [float(x) for x in vec],
                    "metadata": {
                        "document_id": chunk.document_id,
                        "filename": chunk.filename,
                        "page": chunk.page_number,
                        "section": chunk.section,
                        "chunk_index": chunk.chunk_index,
                    },
                }
            self._save()

    def delete_document(self, document_id: str) -> None:
        stale = [rid for rid, rec in self._records.items() if rec["metadata"].get("document_id") == document_id]
        if not stale:
            logger.info("No vectors to delete for document %s", document_id)
            return
        with self._lock:
            for rid in stale:
                self._records.pop(rid, None)
            self._save()

    def query(
        self,
        text: str,
        *,
        top_k: int | None = None,
        document_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        settings = get_settings()
        k = top_k or settings.retrieval_top_k
        if not self._records:
            return []
        try:
            query_vec = self._provider.embed_query(text)
        except Exception as exc:
            logger.exception("Embedding query failed")
            raise RetrievalError("Vector search failed. Try again or re-process documents.") from exc

        wanted = set(document_ids) if document_ids else None
        scored: list[tuple[float, str, dict[str, Any]]] = []
        for rec in self._records.values():
            meta = rec["metadata"]
            if wanted is not None and meta.get("document_id") not in wanted:
                continue
            score = _cosine(query_vec, rec["vector"])
            scored.append((score, rec["id"], rec))
        scored.sort(key=lambda item: (-item[0], item[1]))

        hits: list[dict[str, Any]] = []
        for score, _, rec in scored[:k]:
            meta = rec["metadata"]
            page = meta.get("page")
            hits.append(
                {
                    "text": rec["text"],
                    "document_id": meta.get("document_id", ""),
                    "filename": meta.get("filename", ""),
                    "page": None if page in (None, -1) else int(page),
                    "section": meta.get("section") or None,
                    "chunk_index": meta.get("chunk_index"),
                    "score": round(float(score), 4),
                }
            )
        return hits
