import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.schemas import ChatRequest, ChatResponse, ConversationOut, MessageOut, Citation
from app.services import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    return chat_service.chat(
        db,
        question=payload.question,
        conversation_id=payload.conversation_id,
        document_ids=payload.document_ids,
    )


@router.post("/stream")
def chat_stream(payload: ChatRequest):
    def event_gen():
        answer_parts: list[str] = []
        citations: list[Citation] = []
        for kind, value in chat_service.stream_tokens(payload.question, payload.document_ids):
            if kind == "meta":
                citations = value
                yield f"data: {json.dumps({'type': 'citations', 'citations': [c.model_dump() for c in citations]})}\n\n"
            else:
                answer_parts.append(value)
                yield f"data: {json.dumps({'type': 'token', 'token': value})}\n\n"
        db = SessionLocal()
        try:
            conv_id = chat_service.save_streamed_turn(
                db,
                question=payload.question,
                answer="".join(answer_parts),
                citations=citations,
                conversation_id=payload.conversation_id,
            )
            yield f"data: {json.dumps({'type': 'done', 'conversation_id': conv_id})}\n\n"
        finally:
            db.close()

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.get("/history", response_model=list[ConversationOut])
def history(conversation_id: str | None = None, db: Session = Depends(get_db)):
    convos = chat_service.list_history(db, conversation_id)
    out: list[ConversationOut] = []
    for c in convos:
        messages = []
        for m in c.messages:
            citations = []
            if m.citations_json:
                citations = [Citation.model_validate(x) for x in json.loads(m.citations_json)]
            messages.append(
                MessageOut(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    citations=citations,
                    created_at=m.created_at,
                )
            )
        out.append(ConversationOut(id=c.id, title=c.title, created_at=c.created_at, messages=messages))
    return out


@router.delete("/{conversation_id}", status_code=204)
def clear(conversation_id: str, db: Session = Depends(get_db)):
    chat_service.clear_conversation(db, conversation_id)
    return None
