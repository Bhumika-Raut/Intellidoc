from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str
    filename: str
    original_filename: str
    content_type: str
    file_ext: str
    size_bytes: int
    status: str
    chunk_count: int
    page_count: int
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class Citation(BaseModel):
    document_id: str
    filename: str
    page: int | None = None
    section: str | None = None
    chunk_index: int | None = None
    excerpt: str
    score: float | None = None


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    conversation_id: str | None = None
    document_ids: list[str] | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    citations: list[Citation]
    unsupported: bool = False


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    document_ids: list[str] | None = None
    top_k: int = Field(default=8, ge=1, le=20)


class SearchHit(BaseModel):
    document_id: str
    filename: str
    page: int | None = None
    section: str | None = None
    excerpt: str
    score: float | None = None


class CompareRequest(BaseModel):
    document_id_a: str
    document_id_b: str


class CompareSection(BaseModel):
    category: str
    details: str


class CompareResponse(BaseModel):
    document_a: str
    document_b: str
    sections: list[CompareSection]
    summary: str


class InsightItem(BaseModel):
    value: str
    source: str | None = None


class InsightsResponse(BaseModel):
    people: list[InsightItem] = []
    organizations: list[InsightItem] = []
    dates: list[InsightItem] = []
    amounts: list[InsightItem] = []
    technologies: list[InsightItem] = []
    requirements: list[InsightItem] = []
    deadlines: list[InsightItem] = []
    risks: list[InsightItem] = []
    action_items: list[InsightItem] = []


class ActionItem(BaseModel):
    task: str
    description: str
    priority: str
    deadline: str | None = None
    source: str


class ActionItemsResponse(BaseModel):
    items: list[ActionItem]


class SummaryResponse(BaseModel):
    overview: str
    key_points: list[str]
    important_findings: list[str]
    important_numbers: list[str]
    risks: list[str]
    recommendations: list[str]


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    citations: list[Citation] = []
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: datetime | None = None
    messages: list[MessageOut] = []


class DashboardStats(BaseModel):
    documents: int
    total_chunks: int
    questions_asked: int
    ai_summaries: int
    recent_documents: list[DocumentOut]
    recent_questions: list[dict[str, Any]]
    knowledge_base: list[DocumentOut]
