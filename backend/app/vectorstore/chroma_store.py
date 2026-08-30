import logging
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings
from app.core.exceptions import RetrievalError
from app.embeddings.factory import get_embedding_provider
from app.rag.types import Chunk
from app.vectorstore.base import VectorStore

logger = logging.getLogger(__name__)

COLLECTION = "intellidocs_chunks"


class ChromaVectorStore(VectorStore):
    """Optional ChromaDB backend (VECTOR_STORE=chroma). Requires the `chromadb`
    package, which is intentionally NOT in requirements.txt to keep the default
    install lightweight."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = chromadb.PersistentClient(
            path=str(settings.chroma_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        self._embedder = get_embedding_provider()

    def upsert_chunks(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        ids = [f"{c.document_id}:{c.chunk_index}" for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [
            {
                "document_id": c.document_id,
                "filename": c.filename,
                "page": c.page_number if c.page_number is not None else -1,
                "section": c.section or "",
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]
        try:
            embeddings = self._embedder.embed_documents(documents)
            self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
        except Exception as exc:
            logger.exception("Failed to store embeddings")
            raise RetrievalError("Failed to generate or store embeddings for this document.") from exc

    def delete_document(self, document_id: str) -> None:
        try:
            self._collection.delete(where={"document_id": document_id})
        except Exception:
            logger.warning("No vectors to delete for document %s", document_id)

    def query(
        self,
        text: str,
        *,
        top_k: int | None = None,
        document_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        settings = get_settings()
        k = top_k or settings.retrieval_top_k
        try:
            embedding = self._embedder.embed_query(text)
            kwargs: dict[str, Any] = {
                "query_embeddings": [embedding],
                "n_results": k,
                "include": ["documents", "metadatas", "distances"],
            }
            if document_ids:
                kwargs["where"] = {"document_id": {"$in": document_ids}} if len(document_ids) > 1 else {
                    "document_id": document_ids[0]
                }
            result = self._collection.query(**kwargs)
        except Exception as exc:
            logger.exception("Chroma query failed")
            raise RetrievalError("Vector search failed. Try again or re-process documents.") from exc

        hits: list[dict[str, Any]] = []
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        dists = (result.get("distances") or [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            meta = meta or {}
            page = meta.get("page")
            score = 1.0 - float(dist) if dist is not None else None
            hits.append(
                {
                    "text": doc,
                    "document_id": meta.get("document_id", ""),
                    "filename": meta.get("filename", ""),
                    "page": None if page in (None, -1) else int(page),
                    "section": meta.get("section") or None,
                    "chunk_index": meta.get("chunk_index"),
                    "score": round(score, 4) if score is not None else None,
                }
            )
        return hits

