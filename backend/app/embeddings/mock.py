import hashlib
import math

from app.embeddings.base import EmbeddingProvider


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic hashed bag-of-tokens embeddings.

    - Zero downloads and zero model dependencies (no PyTorch), so the full RAG
      pipeline runs and tests pass on a bare `pip install -r requirements.txt`.
    - Output is stable across runs and machines, which makes tests reproducible.
    - Vectors are NOT semantically meaningful: identical tokens score high,
      paraphrases do not. For real semantic retrieval set
      `EMBEDDING_PROVIDER=api` with an embeddings-capable API key.
    """

    def __init__(self, dim: int = 96):
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_query(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "little") % self._dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(t) for t in texts]


# Backwards-compatible alias for the original test provider name.
HashEmbeddingProvider = MockEmbeddingProvider
