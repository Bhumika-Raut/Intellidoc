from app.core.exceptions import AppError
from app.core.security import is_allowed_file, sanitize_filename


def test_sanitize_strips_path_traversal():
    assert ".." not in sanitize_filename("../../etc/passwd.pdf")
    assert sanitize_filename("C:\\\\Windows\\\\file.docx").endswith(".docx")
    assert "/" not in sanitize_filename("a/b/c.txt")


def test_allowed_extensions():
    assert is_allowed_file("spec.pdf", "application/pdf")
    assert is_allowed_file("notes.md", "text/markdown")
    assert is_allowed_file("notes.txt", "text/plain")
    assert is_allowed_file("brief.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    assert not is_allowed_file("malware.exe", "application/octet-stream")
    assert not is_allowed_file("photo.png", "image/png")


def test_upload_validation_rejects_empty():
    from app.services.document_service import validate_upload

    try:
        validate_upload("a.pdf", "application/pdf", 0)
        assert False, "expected error"
    except AppError as exc:
        assert exc.status_code == 400
