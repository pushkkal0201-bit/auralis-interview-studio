# Auralis 3.2 — Source-Based Security Hardening Review

**Review type:** Scoped, source-first hardening based on the publicly available Cloudflare `security-audit-skill` methodology. This is **not** a completed Cloudflare six-phase, independent, multi-agent penetration test, nor a security certification.

Reference: https://github.com/cloudflare/security-audit-skill and `skills/security-audit/SKILL.md`; relevant companion: `AI-AND-LLM.md`.

**Review scope:** Localhost FastAPI API, session ownership, provider dispatch, model-output trust, GitHub / ZIP evidence, local persistence, UI rendering, provider quotas and fallback provenance. We inspected the packaged source at 3.1 as the baseline and tested the 3.2 changes using local dummy data and fake providers; no production API key or user data was used.

## Trust-boundary map

| Boundary | Current control | Limit |
|---|---|---|
| Browser workspace -> saved sessions | 256-bit browser token hashed on server, owner filtered in SQLite queries | Not authentication; localhost-only edition |
| User text -> LLM | CV, JD and responses explicitly marked untrusted, no generic agent tool execution | A model can still make factual grading errors |
| Uploaded Python ZIP -> CodeProof citations | AST-only scan, archive size/file constraints, server-issued owner-bound evidence handle | Not a complete malware/secret scanner |
| External repo URL -> outbound HTTP | strict GitHub owner/repo allowlist, pinned API/codeload hosts, redirect disabled, bounded download | External GitHub availability and trust need independent verification |
| Model output -> permanent report | Pydantic contract, exact answer-ID validation, trajectory consistency checks, limited deterministic numeric sanity checks | Does not prove every domain-specific conclusion correct |
| Browser text -> DOM | `textContent`, `replaceChildren`; restrictive CSP; no executable Markdown interpolation | Browser deployment-specific behavior needs integration tests |
| Live provider usage | Explicit consent and model allowlist, local process-wide call budget, no automatic paid-provider switch | A restart resets the in-memory request budget; provider billing limits remain authoritative |
| Offline continuation | Explicit local rubric questions and unscored provisional reports | Locally generated questions cannot substitute for verified AI assessment |

## Confirmed source-derived product integrity defect and fix

### S-01 — Source evidence could be impersonated by a client-provided reference

**Before:** `Setup.codeproof_refs` accepted unverified dictionaries; `Engine.question()` accepted a model's matching `source_ref_id` as a source citation. A client controlling its own request could forge a path, symbol, and line number; this is evidence-provenance spoofing in the requesting workspace, not a cross-tenant exploit.

**Change:** `Store.source_evidence` is keyed by owner and opaque server handle, issued only after `inspect_zip()` parses the uploaded ZIP or downloaded public repository. `POST /api/sessions` resolves the handle, ignores client-provided references, and marks citations as verified only after that owner-bound lookup. Old sessions without the server verification marker cannot produce CodeProof source citations.

**Regression:** `tests/test_assessment_integrity_v32.py::test_codeproof_citations_require_server_bound_evidence` verifies a forged citation is discarded and cross-owner handles are rejected; the legitimate upload path still works.

## Other applied safeguards

- Redact multiple common embedded key/token patterns from CodeProof snippets, in addition to assignment-based secret redaction. Secret scanning is NOT complete; don't upload credentials.
- Add in-memory process-wide model-call budget (defaults 15/minute, 90/hour); count attempted calls, including connection tests and transcription. Changes do not bypass upstream free-tier quotas.
- Preserve full evidence locally; sample beginning/middle/end rather than only the first 900 characters when grading lengthy interviews. Explicitly mark excerpts.
- Reject model reports with mismatched evidence IDs, contradictory status/score pairs, omitted first/latest scores for multiple-answer 0/4 judgments, and two specific known false electrical-scoring patterns.
- Replace the question X-Ray's speculative competency status with a statement computed from the interview controller's recorded count and rubric.
- On provider failures, label local plan/question/compare fallback, and withhold scores rather than manufacturing a grading result. Retry assessment after recovery.
- Provide concise printed assessment by default; full transcript is available on demand.

## Needs validation / production blockers

1. **Live provider:** No Groq or Hugging Face credential used in this review. Verify actual structured output, cost/quotas, errors, and rubric quality with a test account and non-sensitive CV.
2. **Browser:** Headless Chromium in this environment returned `ERR_BLOCKED_BY_ADMINISTRATOR` for localhost; manually verify microphone, printing, report expansion, and browser preferences on Windows 11/Chrome or Edge.
3. **Deployment:** Local workspace tokens are not user authentication. Before any public or multi-user launch, add SSO/passwordless login, server sessions, hardened authorization and CSRF policy, HTTPS, secret rotation, tenant isolation, throttling persisted across processes and monitoring.
4. **Secure deletion:** SQLite deletion and retention do not erase journal pages, filesystem snapshots, or independently stored backups. A privacy policy and lifecycle design are required for real candidate data.
5. **Secret prevention:** Regex redaction cannot detect every private string. Pre-scan uploads using a dedicated secret-scanning tool, and never rely on snippet redaction alone.
6. **Independent software supply chain:** No dependency CVE scan or independent pentest was run in this environment. Run `pip-audit`, static code review and dependency update process in a properly isolated CI environment; pin CI action revisions and review third-party licenses.
7. **Grading:** The selected physical/electrical sanity checks are deliberate regression guards, **not** a general engineering validator. Model-generated scores must not drive real hiring decisions without independent domain validation and bias/fairness testing.
8. **Full skill execution:** Cloudflare's complete audit requires independent agents and an OS-enforced, network-isolated write-controlled environment with resource limits. Those full conditions were not implemented here; this document does not claim their workflow was completed.

## Reproducible local QA

Run from the inner `auralis` folder with a clean test data directory:

```
python -m pytest -q
node --check app/static/app.js
python -m compileall -q app
```

The tests use fake providers and do not incur API usage. Do not paste real `.env` values into issue reports.
