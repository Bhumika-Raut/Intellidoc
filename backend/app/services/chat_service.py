import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.llm.factory import get_llm_provider
from app.llm.prompts import RAG_SYSTEM, format_context
from app.models.conversation import Conversation, Message
from app.models.query_log import QueryLog
from app.rag.retriever import hits_to_citations, retrieve
from app.schemas import ChatResponse, Citation

logger = logging.getLogger(__name__)

UNSUPPORTED = "I couldn't find enough information in your documents to answer this reliably."


def chat(db: Session, *, question: str, conversation_id: str | None, document_ids: list[str] | None) -> ChatResponse:
    hits = retrieve(question, document_ids=document_ids)
    citations = hits_to_citations(hits)
    if not hits:
        answer = UNSUPPORTED
        unsupported = True
    else:
        context = format_context(hits)
        user = (
            f"QUESTION:\n{question}\n\nCONTEXT:\n{context}\n\n"
            "Answer using only CONTEXT. Cite [n]. If insufficient, use the exact unsupported sentence."
        )
        try:
            answer = get_llm_provider().generate(system=RAG_SYSTEM, user=user)
        except AppError:
            raise
        except Exception as exc:
            logger.exception("Chat generation failed")
            raise AppError("The language model request failed.", status_code=502, code="llm_error") from exc
        unsupported = UNSUPPORTED in answer

    conv = _get_or_create_conversation(db, conversation_id, question)
    db.add(Message(conversation_id=conv.id, role="user", content=question))
    db.add(
        Message(
            conversation_id=conv.id,
            role="assistant",
            content=answer,
            citations_json=json.dumps([c.model_dump() for c in citations]),
        )
    )
    db.add(QueryLog(query=question, kind="chat", conversation_id=conv.id))
    db.commit()
    return ChatResponse(
        conversation_id=conv.id,
        answer=answer,
        citations=citations,
        unsupported=unsupported,
    )


def stream_tokens(question: str, document_ids: list[str] | None):
    hits = retrieve(question, document_ids=document_ids)
    citations = hits_to_citations(hits)
    if not hits:
        yield ("meta", citations)
        yield ("token", UNSUPPORTED)
        return
    context = format_context(hits)
    user = (
        f"QUESTION:\n{question}\n\nCONTEXT:\n{context}\n\n"
        "Answer using only CONTEXT. Cite [n]. If insufficient, use the exact unsupported sentence."
    )
    yield ("meta", citations)
    for token in get_llm_provider().stream(system=RAG_SYSTEM, user=user):
        yield ("token", token)


def save_streamed_turn(
    db: Session,
    *,
    question: str,
    answer: str,
    citations: list[Citation],
    conversation_id: str | None,
) -> str:
    conv = _get_or_create_conversation(db, conversation_id, question)
    db.add(Message(conversation_id=conv.id, role="user", content=question))
    db.add(
        Message(
            conversation_id=conv.id,
            role="assistant",
            content=answer,
            citations_json=json.dumps([c.model_dump() for c in citations]),
        )
    )
    db.add(QueryLog(query=question, kind="chat", conversation_id=conv.id))
    db.commit()
    return conv.id


def list_history(db: Session, conversation_id: str | None = None) -> list[Conversation]:
    stmt = select(Conversation).order_by(Conversation.created_at.desc())
    if conversation_id:
        stmt = stmt.where(Conversation.id == conversation_id)
    return list(db.scalars(stmt).all())


def clear_conversation(db: Session, conversation_id: str) -> None:
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise AppError("Conversation not found.", status_code=404, code="not_found")
    db.delete(conv)
    db.commit()


def _get_or_create_conversation(db: Session, conversation_id: str | None, question: str) -> Conversation:
    if conversation_id:
        conv = db.get(Conversation, conversation_id)
        if conv:
            return conv
    title = question.strip()[:80] or "New conversation"
    conv = Conversation(title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv
