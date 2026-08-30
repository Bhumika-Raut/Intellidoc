import logging
from pathlib import Path

from pypdf import PdfReader
from docx import Document as DocxDocument

from app.rag.types import ExtractedPage

logger = logging.getLogger(__name__)


def extract_text(path: Path, file_ext: str) -> list[ExtractedPage]:
    ext = file_ext.lower()
    if ext == ".pdf":
        return _extract_pdf(path)
    if ext == ".docx":
        return _extract_docx(path)
    if ext in {".txt", ".md"}:
        return _extract_plain(path)
    raise ValueError(f"Unsupported format: {ext}")


def _extract_pdf(path: Path) -> list[ExtractedPage]:
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise ValueError("This PDF could not be read. It may be corrupted or encrypted.") from exc

    pages: list[ExtractedPage] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            logger.warning("Failed to extract text from PDF page %s", i)
            text = ""
        pages.append(ExtractedPage(page_number=i, text=text))
    return pages


def _extract_docx(path: Path) -> list[ExtractedPage]:
    try:
        doc = DocxDocument(str(path))
    except Exception as exc:
        raise ValueError("This DOCX file could not be read.") from exc

    pages: list[ExtractedPage] = []
    current_section = None
    buffer: list[str] = []
    page_num = 1

    def flush() -> None:
        nonlocal buffer, page_num
        text = "\n".join(buffer).strip()
        if text:
            pages.append(ExtractedPage(page_number=page_num, text=text, section=current_section))
            page_num += 1
        buffer = []

    for para in doc.paragraphs:
        style = (para.style.name or "") if para.style else ""
        text = (para.text or "").strip()
        if not text:
            continue
        if style.startswith("Heading"):
            if buffer:
                flush()
            current_section = text
        buffer.append(text)
        # Approximate page breaks so citations have a section/page analog.
        if sum(len(x) for x in buffer) > 2500:
            flush()

    flush()
    if not pages:
        raise ValueError("The document contains no extractable text.")
    return pages


def _extract_plain(path: Path) -> list[ExtractedPage]:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw = path.read_text(encoding="latin-1")
    except Exception as exc:
        raise ValueError("The text file could not be read.") from exc

    sections: list[ExtractedPage] = []
    current_title = None
    buf: list[str] = []
    page = 1

    def flush() -> None:
        nonlocal buf, page
        text = "\n".join(buf).strip()
        if text:
            sections.append(ExtractedPage(page_number=page, text=text, section=current_title))
            page += 1
        buf = []

    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            if buf:
                flush()
            current_title = stripped.lstrip("# ").strip()
        buf.append(line)
        if sum(len(x) for x in buf) > 2500:
            flush()
    flush()
    return sections
