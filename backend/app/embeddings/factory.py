from functools import lru_cache

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.embeddings.api import APIEmbeddingProvider
from app.embeddings.base import EmbeddingProvider
from app.embeddings.mock import MockEmbeddingProvider

__all__ = [
    "EmbeddingProvider",
    "MockEmbeddingProvider",
    "APIEmbeddingProvider",
    "get_embedding_provider",
]


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    """Select the embedding backend from EMBEDDING_PROVIDER.

    - `mock` (default): deterministic local vectors, no downloads, no key.
      Aliases: `hash` (legacy test name), `local` (kept so older .env files
      keep working), `test`.
    - `api`: OpenAI-compatible embeddings endpoint. Keys are read from
      EMBEDDING_API_KEY (preferred) or OPENAI_API_KEY, never from the client.
    """
    settings = get_settings()
    name = settings.embedding_provider.lower().strip()

    if name in {"mock", "hash", "local", "test"}:
        return MockEmbeddingProvider()

    if name in {"api", "openai"}:
        api_key = settings.embedding_api_key or settings.openai_api_key
        if not api_key:
            raise AppError(
                "Embeddings are set to provider 'api' but no key is configured. "
                "Set EMBEDDING_API_KEY (or OPENAI_API_KEY) in the backend .env.",
                status_code=503,
                code="embedding_not_configured",
            )
        base_url = settings.embedding_api_base or settings.openai_base_url or None
        return APIEmbeddingProvider(api_key=api_key, model=settings.embedding_model, base_url=base_url)

    raise AppError(
        f"Unknown EMBEDDING_PROVIDER '{settings.embedding_provider}'. Use 'mock' or 'api'.",
        status_code=500,
        code="bad_configuration",
    )

