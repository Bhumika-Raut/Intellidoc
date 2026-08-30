from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.embeddings.factory import get_embedding_provider
from app.main import create_app
from app.vectorstore.factory import reset_vector_store


def _client() -> TestClient:
    get_settings.cache_clear()
    get_embedding_provider.cache_clear()
    reset_vector_store()
    return TestClient(create_app())


def test_health():
    res = _client().get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_chat_rejects_empty_question():
    res = _client().post("/api/chat", json={"question": ""})
    assert res.status_code == 422


def test_compare_requires_ids():
    res = _client().post("/api/documents/compare", json={})
    assert res.status_code == 422


def test_reject_unsupported_upload():
    res = _client().post(
        "/api/documents/upload",
        files={"file": ("virus.exe", b"MZ", "application/octet-stream")},
    )
    assert res.status_code in (400, 415)


def test_document_crud_and_rag():
    client = _client()
    content = (
        "# Product Technical Specification\n\n"
        "The product uses OAuth 2.0 with PKCE for authentication.\n"
        "Sessions expire after 12 hours. Database migration is required before go-live.\n"
    ).encode()
    res = client.post(
        "/api/documents/upload",
        files={"file": ("product_spec.md", content, "text/markdown")},
    )
    assert res.status_code == 201
    doc_id = res.json()["id"]
    processed = client.post(f"/api/documents/{doc_id}/process")
    assert processed.status_code == 200
    assert processed.json()["status"] == "ready"
    assert processed.json()["chunk_count"] >= 1

    listed = client.get("/api/documents")
    assert any(d["id"] == doc_id for d in listed.json())

    chat = client.post("/api/chat", json={"question": "What authentication mechanism does the product use?"})
    assert chat.status_code == 200
    body = chat.json()
    assert body["citations"]
    assert body["answer"]

    unsupported = client.post(
        "/api/chat",
        json={"question": "unsupported-eval-question about Martian tax law"},
    )
    assert unsupported.status_code == 200
    assert "couldn't find enough information" in unsupported.json()["answer"].lower()

    search = client.post("/api/search", json={"query": "database migration"})
    assert search.status_code == 200
    assert isinstance(search.json(), list)
