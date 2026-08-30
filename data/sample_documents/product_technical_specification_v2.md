# Helios Document API — Product Technical Specification (v2)

**Product:** Helios Document API  
**Version:** 2.0  
**Author:** Sam Okonkwo, Staff Engineer  
**Organization:** Northwind Labs  
**Date:** 22 June 2026

## 1. Overview

Helios v2 is a REST and streaming API that stores documents, extracts text, embeds chunks, and answers questions with retrieval-augmented generation. This specification replaces v1 for new integrations.

## 2. Authentication

Clients authenticate with **OAuth 2.0 Authorization Code + PKCE**.  
Service-to-service calls use short-lived JWT bearer tokens signed with RS256.  
The product **does not** support API keys in query strings.

Token lifetime (changed):

- Access token: **20 minutes**  
- Refresh token: **14 days**

MFA is required for console users who can delete documents.

## 3. Document storage

Uploaded files are stored in object storage. Maximum file size is **50 MB**. Supported types: PDF, DOCX, TXT, and **Markdown**.

Text extraction is **asynchronous**. A background worker writes status `pending → processing → ready | failed`.

## 4. Search

Search is **hybrid**: keyword (`tsvector`) plus **cosine similarity over embeddings**. Default embedding model: `all-MiniLM-L6-v2`. Results include document name, page, excerpt, and score.

## 5. Rate limits

- Standard tier: **120 requests per minute**  
- Internal tier: **600 requests per minute**

Exceeding the limit returns HTTP 429 with a `Retry-After` header.

## 6. Security

TLS 1.2 or higher is required. Data at rest uses AES-256. Audit logs retain document access events for **180 days**.  
Customer documents are isolated per tenant identifier. Encryption keys are not stored in application source.

## 7. New capabilities

- Cited question answering over retrieved chunks.  
- Document comparison between two versions.  
- Structured insight extraction (people, dates, risks).

OCR for scanned PDFs remains out of scope for v2.0.

## 8. Success metrics

- Extraction success rate above 98% for digitally generated PDFs.  
- p95 search latency under **300 ms** (includes embedding query).  
- Citation present on at least 90% of grounded answers in the evaluation set.
