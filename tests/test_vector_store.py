import pytest

from app.core.config import get_settings
from app.core.exceptions import AppError, RetrievalError
from app.embeddings.api import APIEmbeddingProvider
from app.embeddings.base import EmbeddingProvider
from app.embeddings.factory import get_embedding_provider
from app.embeddings.mock import MockEmbeddingProvider
from app.rag.types import Chunk
from app.vectorstore.base import VectorStore
from app.vectorstore.factory import get_vector_store, reset_vector_store
from app.vectorstore.local_store import LocalVectorStore


def _chunks() -> list[Chunk]:
    return [
        Chunk(text="OAuth 2.0 with PKCE protects the public client.", chunk_index=0, page_number=1, section="Security", document_id="doc-a", filename="auth.md"),
        Chunk(text="The database migration must finish before go-live.", chunk_index=1, page_number=2, section="Ops", document_id="doc-a", filename="auth.md"),
        Chunk(text="Quarterly revenue grew driven by expansion customers.", chunk_index=0, page_number=None, section=None, document_id="doc-b", filename="report.md"),
    ]


def test_mock_provider_is_deterministic_and_normalized():
    provider = MockEmbeddingProvider()
    first = provider.embed_query("OAuth tokens")
    second = provider.embed_query("OAuth tokens")
    assert first == second
    assert provider.dimension == 96
    norm = sum(x * x for x in first) ** 0.5
    assert norm == pytest.approx(1.0, abs=1e-9)


def test_provider_factory_defaults_to_mock_and_rejects_unknown():
    get_embedding_provider.cache_clear()
    assert isinstance(get_embedding_provider(), MockEmbeddingProvider)

    get_settings.cache_clear()
    get_embedding_provider.cache_clear()
    import os

    previous = os.environ.get("EMBEDDING_PROVIDER")
    os.environ["EMBEDDING_PROVIDER"] = "yaml-unknowable"
    try:
        with pytest.raises(AppError):
            get_embedding_provider()
    finally:
        if previous is None:
            os.environ.pop("EMBEDDING_PROVIDER", None)
        else:
            os.environ["EMBEDDING_PROVIDER"] = previous
        get_settings.cache_clear()
        get_embedding_provider.cache_clear()


def test_api_provider_requires_key():
    with pytest.raises(RuntimeError):
        APIEmbeddingProvider(api_key="", model="text-embedding-3-small")


def test_local_store_upsert_query_delete_and_persist(tmp_path):
    path = tmp_path / "vectors" / "chunks.json"
    store = LocalVectorStore(path=path, provider=MockEmbeddingProvider())
    assert isinstance(store, VectorStore)

    store.upsert_chunks(_chunks())

    # Exact bag-of-tokens match scores ~1.0 with the deterministic mock provider.
    hits = store.query("The database migration must finish before go-live.", top_k=2)
    assert len(hits) == 2
    assert hits[0]["text"].startswith("The database migration")
    assert hits[0]["score"] == pytest.approx(1.0, abs=0.01)
    assert hits[0]["page"] == 2 and hits[0]["section"] == "Ops"

    # A loosely related query still ranks the right chunk first.
    loose = store.query("finish the database migration", top_k=2)
    assert loose[0]["text"].startswith("The database migration")
    assert loose[0]["score"] > loose[1]["score"]

    scoped = store.query("revenue growth", document_ids=["doc-b"], top_k=5)
    assert len(scoped) == 1 and scoped[0]["document_id"] == "doc-b"

    # Persistence: a fresh instance over the same file sees the same vectors.
    reopened = LocalVectorStore(path=path, provider=MockEmbeddingProvider())
    assert len(reopened.query("PKCE protects the client", top_k=1)) == 1

    reopened.delete_document("doc-a")
    assert reopened.query("PKCE", document_ids=["doc-a"]) == []
    assert len(reopened.query("revenue", top_k=5)) == 1


def test_local_store_empty_returns_no_hits_and_wraps_provider_errors(tmp_path):
    store = LocalVectorStore(path=tmp_path / "chunks.json", provider=MockEmbeddingProvider())
    assert store.query("anything") == []

    class FailingProvider(EmbeddingProvider):
        dimension = 96

        def embed_query(self, text):
            raise RuntimeError("api down")

        def embed_documents(self, texts):
            raise RuntimeError("api down")

    # Upsert wraps provider failures as RetrievalError.
    failing = LocalVectorStore(path=tmp_path / "chunks-failing.json", provider=FailingProvider())
    with pytest.raises(RetrievalError):
        failing.upsert_chunks(_chunks())

    # Query path: a store that loaded persisted vectors but now cannot embed
    # the question must surface a RetrievalError, not a raw RuntimeError.
    healthy = LocalVectorStore(path=tmp_path / "chunks-persisted.json", provider=MockEmbeddingProvider())
    healthy.upsert_chunks(_chunks())
    degraded = LocalVectorStore(path=tmp_path / "chunks-persisted.json", provider=FailingProvider())
    with pytest.raises(RetrievalError):
        degraded.query("hello")


def test_factory_returns_local_store_by_default():
    reset_vector_store()
    store = get_vector_store()
    reset_vector_store()
    assert isinstance(store, LocalVectorStore)
