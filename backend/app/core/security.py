"""Upload and input hardening. Keys never leave the backend process."""

import re
import unicodedata
from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
    "application/octet-stream",  # browsers sometimes omit a precise type
}

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    """Strip path components and normalize to a safe basename.

    Uploaded files are never executed or passed to a shell. We still reject
    traversal (../) and control characters so stored paths stay predictable.
    """
    name = Path(filename.replace("\\", "/")).name
    name = unicodedata.normalize("NFKC", name)
    name = name.strip().replace("\x00", "")
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    stem = _UNSAFE_CHARS.sub("_", stem).strip("._") or "document"
    if len(stem) > 80:
        stem = stem[:80]
    return f"{stem}{suffix}"


def is_allowed_file(filename: str, content_type: str | None) -> bool:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    if content_type and content_type.split(";")[0].strip().lower() not in ALLOWED_CONTENT_TYPES:
        # Extension is authoritative; unknown/empty types are accepted if extension is valid.
        if content_type.split(";")[0].strip():
            return ext in ALLOWED_EXTENSIONS
    return True
