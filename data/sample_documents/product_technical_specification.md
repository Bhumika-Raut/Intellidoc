# Helios Document API — Product Technical Specification (v1)

**Product:** Helios Document API  
**Version:** 1.0  
**Author:** Sam Okonkwo, Staff Engineer  
**Organization:** Northwind Labs  
**Date:** 18 January 2026

## 1. Overview

Helios is a REST API that stores documents, extracts text, and returns search results for internal tools. This specification describes authentication, storage, rate limits, and the v1 feature set.

## 2. Authentication

Clients authenticate with **OAuth 2.0 Authorization Code + PKCE**.  
Service-to-service calls use short-lived JWT bearer tokens signed with RS256.  
The product **does not** support API keys in query strings.

Token lifetime:

- Access token: **15 minutes**  
- Refresh token: **7 days**

## 3. Document storage

Uploaded files are stored in object storage. Maximum file size is **25 MB**. Supported types in v1: PDF, DOCX, and TXT. Markdown is **not** supported in v1.

Text extraction runs synchronously. There is no background worker in v1.

## 4. Search

Search is **keyword-only** (PostgreSQL `tsvector`). There is no vector index and no semantic ranking in v1.

## 5. Rate limits

- Standard tier: **60 requests per minute**  
- Internal tier: **300 requests per minute**

Exceeding the limit returns HTTP 429.

## 6. Security

TLS 1.2 or higher is required. Data at rest uses AES-256. Audit logs retain document access events for **90 days**.

## 7. Known limitations

- No OCR for scanned PDFs.  
- No document comparison.  
- No streaming chat interface.

## 8. Success metrics

- Extraction success rate above 98% for digitally generated PDFs.  
- p95 search latency under **250 ms**.
