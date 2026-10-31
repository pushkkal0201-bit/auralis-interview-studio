# Auralis 2.0 — Technical Architecture

## Runtime

```text
Browser (HTML/CSS/JavaScript) ─── localhost HTTP ─── Python FastAPI
  │                │                                  │
  │                │                                  ├── Documents: PDF/DOCX/TXT extraction
  │                │                                  ├── CodeProof: ZIP → static AST → source refs
  │                │                                  ├── Incident Room: fixed synthetic cases
  │                │                                  ├── Interview Engine (state + ID policy)
  │                │                                  │     ├── CV/JD grounded plan
  │                │                                  │     ├── Question generation + X-Ray
  │                │                                  │     ├── Trace + answer + session state
  │                │                                  │     └── Evidence-grounded assessment
  │                │                                  ├── Agent Skill loader
  │                │                                  ├── Groq provider → GPT-OSS-20B
  │                │                                  ├── Groq audio → Whisper Large V3 Turbo
  │                │                                  ├── SQLite database
  │                │                                  └── Scripted offline demo provider
  │                └── MediaRecorder audio to Whisper (live only)
  └── Browser SpeechSynthesis (selected installed voice)
```

No Node.js, Redis, Docker or GPU is needed for the main application. The browser is a static JavaScript UI. Heavy reasoning is remote (Groq) in live mode.

## Original model harness

`app/engine.py` controls lifecycle and question policies. `app/provider.py` is only an I/O adapter for a model and audio transcription. Structured `Decision` output is validated against Pydantic and then against the known competency IDs, scenario branch IDs and allowed code-reference IDs before being saved. If the model hallucinates a source ref, Auralis suppresses the citation. It never silently claims a citation to nonexistent code.

A question's `xray` object holds `decision`, `competency_id`, `based_on_turn`, `reason`, `difficulty_reason`, optional `source`, and a disclosure that user-facing rationale is not privileged chain-of-thought. The rationale is generated model text and may be imperfect.

The `adaptive-interviewer` Agent Skill follows Agent Skills open-standard `SKILL.md` metadata and is loaded into the live provider's system prompt alongside task policy and a Pydantic JSON schema. It is not an external modified open-source model harness, but an original interview-specific Python orchestrator.

## Source ingestion

`app/codeproof.py` accepts only ZIP files that fit resource limits. It rejects traversal, encrypted input, unsafe archive size, missing Python source and symlinks. It parses `.py` source using Python's `ast.parse` without importing or evaluating candidate code. It extracts a bounded set of functions, line references, snippets and non-authoritative structural indicators. It removes secret-like assignments from snippets and excludes likely credential files. Public GitHub import is restricted to the GitHub REST API + GitHub codeload endpoint; no arbitrary URL is fetched. Private repository access is not implemented.

## Incident Room

`app/incidents.py` defines three fixed synthetic incidents. A selected case overrides the generated scenario facts for that interview. The open-weight LLM receives the selected incident ID and uses bounded scenario context to choose adaptive questions. This does not generate live application telemetry and no attack tools or external production systems are accessed.

## Assessment

Only recorded answer turns count as evidence. The provider is required to cite answer IDs for each competency. `validate_report` rejects nonexisting or cross-competency IDs, nulls out unsupported ratings, labels demo scores absent, and appends context-truncation limitations. Skill DNA is a visualization of this verified structure, not separate AI scoring.

## Data privacy

The app is localhost-only with a single server worker and per-browser random owner-token isolation. Sessions reside in SQLite `.data/auralis.sqlite3`. The app does not encrypt them. CV/job text and project references are passed to Groq when the user explicitly selects live mode and consents. Uploaded audio is sent to Groq only for transcription and is not persisted as a file by Auralis. The key stays in local `.env` and is never returned to the browser.

## Browser API interfaces

- `GET /api/health`: local health + configured flag (never key)
- `GET /api/live/check`: explicit key/model availability check
- `POST /api/documents`: CV text extraction
- `POST /api/codeproof/zip`: safely inspect a small source ZIP
- `POST /api/codeproof/github`: restricted small public repo importer
- `GET /api/incidents`: fixed synthetic incidents
- `POST /api/sessions`: create plan and session
- `POST /api/sessions/{id}/start`: generate first question
- `POST /api/sessions/{id}/actions`: answer, clarify, hint, skip
- `POST /api/sessions/{id}/finish`: generate evidence-linked report
- `POST /api/transcribe/{id}`: Groq Whisper for consented live session
- `POST /api/sessions/{id}/retry`: practice existing weakness
- `GET /api/sessions/{id}/export`: JSON export
- `DELETE /api/sessions/{id}`: remove session row

This is a local hackathon system. Production hosting requires login, per-account permissions, consent review, rate limiting, storage encryption, monitoring and operational security review.


### One-provider, multi-open-model design

Frontend chooses `ai_model` in Setup. Pydantic whitelists approved IDs.
`Engine.generate_for()` binds the selected model into the call context without mutating shared provider state.
`GroqProvider` validates it again and sends it to the Groq chat-completions API.
All subsequent question/retry/report calls follow the session's saved model.
Whisper transcription stays on Groq independent of which text model is selected.
No OpenAI proprietary GPT API or xAI Grok service is used.


## v3.0 Multi-provider open-weight GPT-OSS inference

```
Browser (HTML/CSS/JS, voice recognition and synthesis)
    -> FastAPI local-boundary API
        -> Engine (state machine, rubric, CodeProof, Incident Room, X-Ray)
            -> GroqProvider: GPT-OSS 20B/120B (and optional Qwen preview)
            -> HuggingFaceProvider: GPT-OSS 120B/20B via HF inference router
            -> DemoProvider: clearly labelled scripted flow only
        -> SQLite session storage
```

The browser never receives the provider key. Per-session `provider` and `ai_model`
are validated against explicit allowlists, persisted in each session, and used
for interview plan, follow-up, report and targeted retries. The model can request
question strategies but the application validates source reference IDs, rubric
competencies, and answer-evidence IDs before saving the result. A failed live call
is an error, not an undisclosed scripted fallback.

Hugging Face inference follows the documented `/v1/chat/completions` API with
`response_format=json_schema` for GPT-OSS 120B through Fireworks. A second
HF routed GPT-OSS 20B model uses JSON object mode plus Pydantic validation.
Provider feature availability is subject to current HF inference support.
