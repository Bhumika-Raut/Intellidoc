# Software Project Requirements — Atlas Campus Portal v1.2

**Document ID:** SPR-2026-041  
**Owner:** Alex Rivera, Product Engineering  
**Organization:** Northwind Labs  
**Status:** Approved for implementation  
**Effective date:** 1 September 2026  
**Review deadline:** 15 October 2026

## 1. Purpose

This document specifies functional and non-functional requirements for the Atlas Campus Portal, a web application that lets students, faculty, and staff access academic records, submit requests, and receive notifications.

## 2. Stakeholders

- Product owner: Alex Rivera  
- Security lead: Priya Nair  
- Registrar office: Jordan Hale  
- Vendor: Northwind Labs

## 3. Authentication and access

REQ-AUTH-01. The system shall authenticate users with **OAuth 2.0 Authorization Code + PKCE**.  
REQ-AUTH-02. **Multi-factor authentication (MFA)** is required for all administrator roles and for any user accessing financial aid data.  
REQ-AUTH-03. Session tokens shall expire after **12 hours**. Refresh tokens shall expire after **14 days**.  
REQ-AUTH-04. Failed login attempts: lock the account for 15 minutes after **5 consecutive failures**.

## 4. Core features

REQ-CORE-01. Students can view unofficial transcripts and current enrollment.  
REQ-CORE-02. Faculty can submit grades for a section until the registrar lock date.  
REQ-CORE-03. Staff can file facilities tickets and track status.  
REQ-CORE-04. The portal shall send email notifications for grade posts and ticket updates.

## 5. Data and integrations

REQ-DATA-01. Student records are sourced from the Student Information System via a read-only REST API.  
REQ-DATA-02. A **database migration** from the legacy MySQL 5.7 schema to PostgreSQL 16 must complete before go-live.  
REQ-DATA-03. Personally identifiable information shall be encrypted at rest using AES-256.

## 6. Non-functional requirements

REQ-NFR-01. p95 API latency under 400 ms for authenticated read endpoints.  
REQ-NFR-02. Availability target: 99.5% during academic terms.  
REQ-NFR-03. Accessibility: WCAG 2.2 AA.

## 7. Budget and timeline

- Implementation budget: **USD 185,000**  
- Go-live target: **12 January 2027**  
- Soft launch with 200 beta users: **1 December 2026**

## 8. Risks

- RISK-01. SIS vendor API rate limits (120 requests/minute) may delay transcript generation.  
- RISK-02. Incomplete mapping of legacy grade codes could block the database migration.  
- RISK-03. MFA enrollment friction may increase help-desk volume during the first two weeks.

## 9. Open action items

1. Priya Nair: finalize MFA vendor selection by **20 September 2026**.  
2. Engineering: complete PostgreSQL migration rehearsal on staging.  
3. Jordan Hale: confirm registrar lock-date calendar for Fall 2026.

## 10. Out of scope

Mobile native applications, payment processing, and live video proctoring are out of scope for v1.2.
