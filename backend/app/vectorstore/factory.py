from functools import lru_cache

from app.core.config import get_settings
from app.vectorstore.base import VectorStore


@lru_cache
def get_vector_store() -> VectorStore:
    """Return the configured vector store backend (VECTOR_STORE env setting)."""
    settings = get_settings()
    backend = settings.vector_store.lower().strip()
    if backend == "chroma":
        from app.vectorstore.chroma_store import ChromaVectorStore  # optional dependency

        return ChromaVectorStore()
    from app.vectorstore.local_store import LocalVectorStore

    return LocalVectorStore()


def reset_vector_store() -> None:
    """Drop the cached store instance (used by tests and config changes)."""
    get_vector_store.cache_clear()
