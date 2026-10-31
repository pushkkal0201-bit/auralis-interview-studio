# Auralis 5.7.2 — focused security hardening review

**Review basis:** Cloudflare's open-source `security-audit-skill` trust-boundary
methodology, especially its AI/LLM, authorization, browser, resource-spend, and
data-lifecycle prompts. This is **not** an official Cloudflare audit, an external
penetration test, or a complete six-phase independently verified review.

## Covered source areas
- `app/main.py`: FastAPI endpoints, session identity, host/origin control,
  protected mutations, provider spend paths, request size limit, and response headers.
- `app/auth57.py` and `app/auth_abuse.py`: delegated Supabase authentication,
  account throttling and session refresh behavior.
- `app/usage_budget.py`, `app/provider.py`, `app/engine.py`: per-account shared
  model budgets, strict inference handling, and interrupted-turn recovery.
- `app/store.py`, `app/database.py`, `scripts/retention_maintenance.py`:
  owner-scoped records, PostgreSQL translation and retention.
- `app/codeproof.py`, `app/practical_lab.py`, `app/static/*.js`: archive inspection,
  restricted coding evaluation and safe user-output rendering.

## Improvements made
1. **Exact-origin protection:** reject non-matching scheme + authority on
   browser Origin requests. In production reject cross-site/same-site Fetch
   Metadata on mutations; retain localhost testing support.
2. **Account request rate limits:** database-shared per-identity and global
   request budgets for signup, login, refresh, password recovery, password
   change and account closure; retain only digests in the counter table.
   Counters are an anti-abuse supplement, not WAF-grade bot protection.
3. **Spend accounting:** reject unsupported provider checks before consuming
   a paid-model request budget. Hosted tests prohibit Hugging Face checks
   when only live Groq is permitted.
4. **Security headers:** HSTS in production, denial of iframe embedding,
   restricted browser permissions, existing CSP and no-store maintained.
5. **Deletion consistency:** delete the current owner's AI usage rows
   when they choose the full Auralis-data deletion route.
6. **Retention operations:** introduce a one-shot maintenance command
   for scheduled expiry rather than relying solely on process restarts.

## Pre-existing protections retained (not newly certified)
- Verified Supabase identities and account-scoped data access in hosted mode.
- Pinned external GitHub URL/API routes and bounded zip extraction.
- Restricted Python expression evaluator, no arbitrary execution in CodeProof.
- Input length validation, upload-size limits and selected safe DOM APIs.
- Shared live-AI request budgets (the earlier 5.7.1 implementation).

## Deployment blockers and checks requiring owner validation
- Real Supabase signup, reset email, MFA policy, and request volume limits.
- Actual managed PostgreSQL transactions, schema, migrations, backup/restore,
  pool size, failover and performance under concurrency.
- Live Groq model inference and provider-side token, spending, and outage caps.
- Domain HTTPS, trusted proxy/TLS termination, DNS, WAF/bot protection,
  cross-origin behavior, logging and breach response.
- Two-account and instructor/student isolation scenarios against the deployed
  service; security headers and cookie settings in real browsers.
- Data protection policies, consent text, export/deletion requests and
  third-party processing legal review.

## Not fully solved by code alone
- Compromised authorized users remain capable of using their own allowances.
- A determined botnet can exhaust the global sign-in budget before an edge WAF
  stops it; configure managed protection and provider-side quotas.
- No production identity/database/provider credentials were available here;
  tests use synthetic principals. Do not claim independent certification.
- This was a **focused source review**, not Cloudflare's complete six-phase
  audit with independent verifier agents and validated findings JSON.

## Suggested protected rollout
Private staging deployment -> two-account acceptance tests -> backup/restore
exercise -> external security review -> limited invite-only pilot -> public
registration after operational sign-off.
