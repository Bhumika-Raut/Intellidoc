from abc import ABC, abstractmethod
from typing import Any

from app.rag.types import Chunk


class VectorStore(ABC):
    """Storage/search contract for document chunks. Implementations are swappable
    via VECTOR_STORE: `local` (default, dependency-free) or `chroma` (optional)."""

    @abstractmethod
    def upsert_chunks(self, chunks: list[Chunk]) -> None: ...

    @abstractmethod
    def delete_document(self, document_id: str) -> None: ...

    @abstractmethod
    def query(
        self,
        text: str,
        *,
        top_k: int | None = None,
        document_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]: ...
