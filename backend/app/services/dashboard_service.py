from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.query_log import QueryLog
from app.schemas import DashboardStats, DocumentOut
from app.services.document_service import list_documents, sum_chunks


def get_dashboard(db: Session) -> DashboardStats:
    docs = list_documents(db)
    questions = db.scalar(select(func.count()).select_from(QueryLog).where(QueryLog.kind == "chat")) or 0
    summaries = db.scalar(select(func.count()).select_from(QueryLog).where(QueryLog.kind == "summary")) or 0
    recent_q = list(
        db.scalars(select(QueryLog).where(QueryLog.kind == "chat").order_by(QueryLog.created_at.desc()).limit(8)).all()
    )
    return DashboardStats(
        documents=len(docs),
        total_chunks=int(sum_chunks(db)),
        questions_asked=int(questions),
        ai_summaries=int(summaries),
        recent_documents=[DocumentOut.model_validate(d) for d in docs[:6]],
        recent_questions=[{"id": q.id, "query": q.query, "created_at": q.created_at} for q in recent_q],
        knowledge_base=[DocumentOut.model_validate(d) for d in docs],
    )
