import json
import logging

from sqlalchemy.orm import Session

from app.core.exceptions import AppError, LLMError
from app.llm.factory import get_llm_provider
from app.llm.prompts import (
    ACTIONS_SYSTEM,
    COMPARE_SYSTEM,
    INSIGHTS_SYSTEM,
    SUMMARY_SYSTEM,
    format_context,
)
from app.models.query_log import QueryLog
from app.rag.retriever import document_context, retrieve
from app.schemas import (
    ActionItem,
    ActionItemsResponse,
    CompareResponse,
    CompareSection,
    InsightItem,
    InsightsResponse,
    SearchHit,
    SummaryResponse,
)
from app.services.document_service import get_document, require_ready

logger = logging.getLogger(__name__)


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        return data
    except json.JSONDecodeError as exc:
        raise LLMError("The model returned invalid structured output. Please retry.") from exc


def summarize_document(db: Session, document_id: str) -> SummaryResponse:
    doc = get_document(db, document_id)
    require_ready(doc)
    hits = document_context(
        document_id,
        "executive summary key points findings numbers risks recommendations",
        top_k=16,
    )
    if not hits:
        raise AppError("No searchable content is available for this document.", status_code=422)
    user = f"Document: {doc.original_filename}\n\nCONTEXT:\n{format_context(hits)}"
    raw = get_llm_provider().generate(system=SUMMARY_SYSTEM, user=user, json_mode=True)
    data = _parse_json(raw)
    db.add(QueryLog(query=f"summarize:{doc.original_filename}", kind="summary"))
    db.commit()
    return SummaryResponse(
        overview=str(data.get("overview") or "Not found in the document."),
        key_points=_str_list(data.get("key_points")),
        important_findings=_str_list(data.get("important_findings")),
        important_numbers=_str_list(data.get("important_numbers")),
        risks=_str_list(data.get("risks")),
        recommendations=_str_list(data.get("recommendations")),
    )


def compare_documents(db: Session, document_id_a: str, document_id_b: str) -> CompareResponse:
    if document_id_a == document_id_b:
        raise AppError("Select two different documents to compare.", status_code=400)
    a = get_document(db, document_id_a)
    b = get_document(db, document_id_b)
    require_ready(a)
    require_ready(b)
    query = "requirements features policies authentication security deadlines changes"
    hits_a = document_context(document_id_a, query, top_k=10)
    hits_b = document_context(document_id_b, query, top_k=10)
    user = (
        f"DOCUMENT A ({a.original_filename}):\n{format_context(hits_a)}\n\n"
        f"DOCUMENT B ({b.original_filename}):\n{format_context(hits_b)}"
    )
    raw = get_llm_provider().generate(system=COMPARE_SYSTEM, user=user, json_mode=True)
    data = _parse_json(raw)
    sections = [
        CompareSection(category=str(s.get("category", "Note")), details=str(s.get("details", "")))
        for s in data.get("sections") or []
        if isinstance(s, dict)
    ]
    db.add(QueryLog(query=f"compare:{a.original_filename}|{b.original_filename}", kind="compare"))
    db.commit()
    return CompareResponse(
        document_a=a.original_filename,
        document_b=b.original_filename,
        sections=sections,
        summary=str(data.get("summary") or ""),
    )


def extract_insights(db: Session, document_id: str) -> InsightsResponse:
    doc = get_document(db, document_id)
    require_ready(doc)
    hits = document_context(
        document_id,
        "people organizations dates amounts technologies requirements deadlines risks action items",
        top_k=16,
    )
    user = f"Document: {doc.original_filename}\n\nCONTEXT:\n{format_context(hits)}"
    raw = get_llm_provider().generate(system=INSIGHTS_SYSTEM, user=user, json_mode=True)
    data = _parse_json(raw)
    db.add(QueryLog(query=f"insights:{doc.original_filename}", kind="insights"))
    db.commit()
    return InsightsResponse(
        **{key: _insight_list(data.get(key)) for key in InsightsResponse.model_fields}
    )


def action_items(db: Session, document_id: str) -> ActionItemsResponse:
    doc = get_document(db, document_id)
    require_ready(doc)
    hits = document_context(document_id, "action items tasks must should deadline owner priority", top_k=14)
    user = f"Document: {doc.original_filename}\n\nCONTEXT:\n{format_context(hits)}"
    raw = get_llm_provider().generate(system=ACTIONS_SYSTEM, user=user, json_mode=True)
    data = _parse_json(raw)
    items = []
    for item in data.get("items") or []:
        if not isinstance(item, dict):
            continue
        items.append(
            ActionItem(
                task=str(item.get("task") or "Untitled task"),
                description=str(item.get("description") or ""),
                priority=str(item.get("priority") or "Medium"),
                deadline=item.get("deadline"),
                source=str(item.get("source") or doc.original_filename),
            )
        )
    db.add(QueryLog(query=f"actions:{doc.original_filename}", kind="actions"))
    db.commit()
    return ActionItemsResponse(items=items)


def semantic_search(db: Session, query: str, document_ids: list[str] | None, top_k: int) -> list[SearchHit]:
    hits = retrieve(query, document_ids=document_ids, top_k=top_k)
    db.add(QueryLog(query=query, kind="search"))
    db.commit()
    return [
        SearchHit(
            document_id=h.get("document_id") or "",
            filename=h.get("filename") or "document",
            page=h.get("page"),
            section=h.get("section"),
            excerpt=(h.get("text") or "")[:500],
            score=h.get("score"),
        )
        for h in hits
    ]


def _str_list(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)]


def _insight_list(value) -> list[InsightItem]:
    items: list[InsightItem] = []
    if not isinstance(value, list):
        return items
    for item in value:
        if isinstance(item, str):
            items.append(InsightItem(value=item))
        elif isinstance(item, dict) and item.get("value"):
            items.append(InsightItem(value=str(item["value"]), source=item.get("source")))
    return items
