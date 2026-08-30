# IntelliDocs — interview notes

Answers below refer to **this repository**, not a generic RAG textbook.

## 1. Why did you use RAG?

The knowledge lives in user-uploaded files that change over time and will not fit reliably in a prompt. RAG retrieves only the chunks that match the question (`app/rag/retriever.py` + the pluggable vector store), then the LLM writes from that window. That gives citations, lower token cost, and a clear refusal path when nothing relevant is retrieved.

## 2. Why not send the whole document to the LLM?

A 50-page spec plus conversation history blows past cheap context windows, costs more, and still lets the model ignore the middle of the file. Ingestion chunks at about 900 characters with overlap (`CHUNK_SIZE` / `CHUNK_OVERLAP` in settings). Chat sends **top-k retrieved chunks** (default 5), not the file.

## 3. What are embeddings?

Numeric vectors for text. Similar meanings land close together in cosine space. The provider layer (`app/embeddings`) has two implementations behind one `EmbeddingProvider` interface: `MockEmbeddingProvider` — a deterministic hashed bag-of-tokens encoder used for local dev and CI so nothing heavy (no PyTorch) is ever downloaded — and `APIEmbeddingProvider`, an OpenAI-compatible embeddings client for production, selected with `EMBEDDING_PROVIDER=api` plus `EMBEDDING_API_KEY`. Adding a third backend is one new class plus one entry in the factory.

## 4. How does vector search work?

Every store implements the `VectorStore` interface (`app/vectorstore/base.py`). The default `LocalVectorStore` embeds the question, computes cosine similarity against the persisted chunk vectors in pure Python, and returns text plus metadata with a rounded `score`. Filters can restrict to selected `document_ids`. The optional `ChromaVectorStore` implements the same interface with cosine distance converted to `score = 1 - distance`.

## 5. What is chunking?

`chunk_pages` walks extracted pages/sections and splits on length while preferring `\\n\\n` or `". "` boundaries, then applies overlap so sentences at boundaries are not lost. Each `Chunk` stores `document_id`, `filename`, `page_number`, `section`, `chunk_index`.

## 6. How did you reduce hallucinations?

- System prompt `RAG_SYSTEM` forbids claims outside CONTEXT.
- Fixed refusal: *I couldn't find enough information in your documents to answer this reliably.*
- Weak-score filter (`MIN_SCORE` in `retriever.py`) drops very dissimilar hits when stronger ones exist.
- Summaries, compare, insights, and actions are JSON structured outputs grounded in retrieved excerpts, not the whole disk file.

## 7. How are citations generated?

Retrieval hits are numbered in `format_context` as `[1] filename, page N`. The model is told to cite those numbers. The UI does not trust the model for provenance: it **always renders the retrieved chunks** (filename, page, section, excerpt, score) from the retriever payload.

## 8. Why a pluggable vector store instead of just ChromaDB?

ChromaDB is a good default for production-scale demos, but its dependency tree is heavy (it pulls a large ML stack), which made install and Docker builds slow and forced a PyTorch download nobody needs for a demo. The default `LocalVectorStore` implements the same `VectorStore` interface in pure Python with JSON persistence — zero extra dependencies, survives restarts, easy to inspect — and `VECTOR_STORE=chroma` swaps in `ChromaVectorStore` when it is warranted. The interface is the swap point; a pgvector backend would be a third implementation.

## 9. How would you scale this system?

Split API and workers; run ingestion on a queue; put SQLite’s workload on PostgreSQL; run the vector store (Chroma or pgvector) as a service; cache embeddings by content hash (we already store `checksum` on `documents`); add horizontal API replicas behind the same object store.

## 10. How would you handle millions of documents?

Sharded vector indexes, per-tenant collections, incremental ingestion, hierarchical retrieval (doc-level then chunk-level), and not embedding unchanged files (`checksum`). Background workers replace in-process `BackgroundTasks`.

## 11. How would you evaluate RAG quality?

`backend/eval/evaluate.py` already scores retrieval hit rate (expected terms in chunks), answer relevance, citation presence, and unsupported refusal. Next step: a labeled set with gold document ids, nDCG, faithfulness vs. context, and human spot checks.

## 12. What happens if retrieval returns irrelevant chunks?

The model can still be misled. Mitigations here: score floor, small `top_k`, strict system prompt, and UI that shows excerpts so a user can see a bad retrieve. Production next step: reranker and “answerability” classifier before generation.

## 13. How would you reduce LLM costs?

Local embeddings (default), retrieve-then-generate instead of stuffing files, `temperature=0.1`, cache summaries by document checksum, skip LLM on empty retrieval (chat already short-circuits to the refusal string when there are no hits), Groq/small models for drafts.

## 14. How would you secure user documents?

Today: keys only on the backend, allowlisted types, size limits, sanitized names, CORS, generic 500s. Next: authN/Z, per-user rows, encryption at rest, signed download URLs, virus scanning, audit logs (we already log queries in `query_logs`).

## 15. How would you implement authentication?

JWT or session cookies in FastAPI middleware; `user_id` on `documents` and vector-store metadata; frontend login before API calls. Do not put secrets in `NEXT_PUBLIC_*`.

## 16. How would you migrate SQLite to PostgreSQL?

`DATABASE_URL` is already a SQLAlchemy URL. `connect_args` for `check_same_thread` apply only to SQLite (`app/core/database.py`). Models use portable types (`String`, `Text`, `DateTime(timezone=True)`). Point `DATABASE_URL` at Postgres, `alembic upgrade`, copy files to object storage.

## 17. How would you implement hybrid search?

Keep the vector store (or pgvector) for dense retrieval; add BM25 (e.g. SQLite FTS5 or Elasticsearch) on the same chunk text; merge with RRF (reciprocal rank fusion). The search API already returns scored passages — you would combine two ranked lists there.

## 18. How would you add reranking?

After `top_k=20` vector hits, score query–chunk pairs with a cross-encoder and keep 5. Plug that between `VectorStore.query` and `format_context` so the LLM sees a tighter window.

## 19. How would you support images/tables in PDFs?

Digital text: improve table extraction (e.g. pdfplumber). Scans: OCR (Tesseract/cloud). Figures: multimodal embeddings or captioning, stored as chunks with `page` metadata. This repo’s PDF path is `pypdf` text only — image-only PDFs fail with a clear “no text extracted” error.

## 20. What would you improve in version 2?

Auth, PostgreSQL, hybrid search + rerank, OCR, real background workers, tenant isolation, and a labeled eval set. Product-wise: per-document chat scope is already supported via `document_ids` on `/api/chat`.
