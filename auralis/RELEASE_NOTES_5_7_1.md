# Auralis 5.7.1 — Production Hardening

Built on Auralis 5.7; source, UI and existing AI interview flows preserved.

## Fixes and new production safeguards
- Transactionally persisted per-account and global Groq call counters (PostgreSQL hosted mode).
- Allowed-instructor Supabase Auth UUID checks for cohort administration; student invitation access retained.
- `/api/ready` signals database failures without exposing credentials or stack traces.
- Optional password-confirmed account closure and Auth user deletion through a server-only Supabase legacy service-role key.
- Cloud privacy copy distinguishes hosted PostgreSQL from local SQLite.
- Release metadata synchronized with server and Windows launcher.
- Separate non-destructive cloud preflight and optional isolated real-PostgreSQL integration smoke test.
- Regression suite expanded to 163 passing tests (plus one optional isolated-PostgreSQL test skipped without credentials).

## Critical limitations
- No real Supabase Auth, managed PostgreSQL, Groq paid inference, or Render backup restoration was available during testing.
- No verified institution role delegation, production billing or full security certification.
- External Auth deletion and internal database deletion are not cross-service atomic.
- Before opening the application to real students, follow `DEPLOY_5_7_1.md` and complete live acceptance testing.
