import logging

from app.embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)

_BATCH_SIZE = 64


class APIEmbeddingProvider(EmbeddingProvider):
    """Embeddings from any OpenAI-compatible `/v1/embeddings` API.

    Used when `EMBEDDING_PROVIDER=api`. The API key lives only in backend
    environment variables and is never sent to the frontend. Errors bubble up
    as plain exceptions and are converted to `RetrievalError` by the vector
    store layer, keeping this class free of HTTP/framework concerns.
    """

    def __init__(self, api_key: str, model: str = "text-embedding-3-small", base_url: str | None = None):
        if not api_key:
            raise RuntimeError("APIEmbeddingProvider requires an API key.")
        from openai import OpenAI  # lazy: keeps import cost out of tests/mock mode

        self._model = model
        self._client = OpenAI(api_key=api_key, base_url=base_url or None)
        self._dim: int | None = None

    @property
    def dimension(self) -> int:
        # Determined lazily from a probe call; no per-model dimension table to maintain.
        if self._dim is None:
            self._dim = len(self.embed_query("dimension probe"))
        return self._dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), _BATCH_SIZE):
            batch = texts[start : start + _BATCH_SIZE]
            try:
                response = self._client.embeddings.create(model=self._model, input=batch)
            except Exception as exc:
                logger.warning("Embedding API request failed: %s", exc)
                raise
            vectors.extend(item.embedding for item in response.data)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
