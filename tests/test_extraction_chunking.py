from pathlib import Path

from app.rag.chunking import chunk_pages
from app.rag.cleaning import clean_text
from app.rag.extraction import extract_text
from app.rag.types import ExtractedPage


def test_clean_text_normalizes_whitespace():
    assert "  " not in clean_text("hello   world\r\n\r\n\r\nok")


def test_chunking_preserves_metadata():
    pages = [
        ExtractedPage(page_number=1, text="A" * 400 + ". " + "Authentication uses OAuth 2.0 with PKCE. " * 20, section="Security"),
        ExtractedPage(page_number=2, text="Database migration must complete before go-live.", section="Ops"),
    ]
    chunks = chunk_pages(pages, document_id="doc-1", filename="spec.md", chunk_size=200, overlap=40)
    assert chunks
    assert all(c.document_id == "doc-1" for c in chunks)
    assert any(c.page_number == 1 for c in chunks)
    assert any("OAuth" in c.text for c in chunks)


def test_extract_markdown(tmp_path: Path):
    path = tmp_path / "sample.md"
    path.write_text("# Title\n\nHello world.\n\n## Security\n\nUse OAuth 2.0.\n", encoding="utf-8")
    pages = extract_text(path, ".md")
    joined = "\n".join(p.text for p in pages)
    assert "OAuth 2.0" in joined
