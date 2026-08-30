from dataclasses import dataclass, field


@dataclass
class ExtractedPage:
    page_number: int | None
    text: str
    section: str | None = None


@dataclass
class Chunk:
    text: str
    chunk_index: int
    page_number: int | None = None
    section: str | None = None
    document_id: str = ""
    filename: str = ""
    metadata: dict = field(default_factory=dict)
