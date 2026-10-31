# RoleReady Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver a runnable local interview app and tested source ZIP.
**Architecture:** FastAPI routes call a stateful interview service with SQLite persistence and a provider abstraction. Live Groq and explicit scripted demo implement the same validated schemas. Vanilla JS owns microphone, speech, screens and print export.
**Tech Stack:** Python 3.11+, FastAPI, Pydantic, HTTPX, SQLite, pypdf, python-docx, pytest.
**Spec:** docs/superpowers/specs/2026-10-26-roleready.md

## Global Constraints
No Node.js needed by user. Free-tier-compatible and no silent provider fallback. Keys server-side only. Localhost single-worker deployment. Plan and spec capture the user's request to implement all previously discussed features now.

## Review Focus
- Malformed upstream responses must not advance or corrupt a session.
- Retries and concurrent submissions must not create duplicate turns.
- Evidence cannot cite invented answer IDs or quotes.
- Microphone denial, expired timers and rate limits must preserve work.
- Unusual roles and unsupported uploads must produce actionable feedback.

### Task 1: Contracts and interview controller
Files: app/schemas.py, app/store.py, app/engine.py, app/demo.py, tests/test_flow.py.
Interfaces: create_app(data_dir, provider=None); provider.generate(task, context, schema); store.load/save with revision; session prepare/start/action/finish.
- [x] Write API tests for prepare/start/answer/clarify/finish, isolation, idempotency, deadline, report evidence, malformed provider rollback, and retries.
- [x] Run pytest, confirm missing implementation failure.
- [x] Implement schema-validated controller and owner-scoped SQLite persistence.
- [x] Run pytest until green and record evidence.

### Task 2: Integration boundaries
Files: app/provider.py, app/documents.py, app/main.py, tests/test_boundaries.py.
Interfaces: extract_document(filename, bytes) -> text; GroqProvider.generate/transcribe; REA evidence normalization.
- [x] Write tests for extraction, MIME/size limits, provider errors, JSON validation, origin protection, and evidence import.
- [x] Implement HTTP boundary and provider with timeouts, readable quota errors, bounded uploads and explicit consent.
- [x] Verify tests and live-shape mocked HTTP integration. No live key is available in this session.

### Task 3: Browser experience
Files: app/static/index.html, style.css, app.js, tests/browser_smoke.cjs.
Interfaces: same-origin /api endpoints with owner bearer token, session IDs and request IDs.
- [x] Write browser workflow test for demo creation, spoken question controls, answer, finish, retry, history and deletion.
- [x] Implement responsive UI with accessible status, recorder, synthesis, reviewable transcription, replay, comparison, and report export.
- [x] Run browser smoke and inspect desktop/mobile rendering.

### Task 4: Delivery and review
Files: README.md, requirements.txt, scripts, examples, docs, LICENSE, THIRD_PARTY_NOTICES.md.
- [x] Provide Windows setup/start/test scripts and cross-platform instructions.
- [x] Run full tests, fresh reviewer, fix important issues with regressions.
- [x] Package clean ZIP excluding environment, secrets, data and caches; persist deliverable.
