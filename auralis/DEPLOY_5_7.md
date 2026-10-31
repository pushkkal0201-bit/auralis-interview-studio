# Auralis 5.7 | Hosted FastAPI + Supabase Auth + PostgreSQL

Auralis 5.7 adds verified Supabase user ownership, cookie-backed refresh sessions, PostgreSQL storage adapters, and strict Groq interview generation.
**Do not invite real users until you verify the hosted deployment, data segregation, backups and privacy controls yourself.** This release is a production foundation, not an independently certified public SaaS system.

## 1. Preparation (Windows)

1. Install Python 3.11.9 and Git, unzip Auralis 5.7.
2. Run `setup.bat`, `test.bat`. Local mode still uses SQLite for development.
3. Make a **private** GitHub repository and ensure `.env`, `.data`, `.venv`, database snapshots and keys are ignored by Git.
4. Push only the `auralis/` source (so `requirements.txt` and `app/` are at the GitHub repository root).

## 2. Supabase account project

1. Open https://supabase.com/dashboard and create a project in an appropriate region.
2. In **Authentication → Providers → Email**, enable email sign-in and confirm-email verification. Configure a reliable SMTP provider before inviting real users (the default mail service has limitations).
3. Set **Authentication → URL Configuration → Site URL** to your final HTTPS Render URL. Add the exact same URL to the redirect allowlist for password recovery.
4. Copy the project URL (`https://...supabase.co`) and **publishable/anon** key (NOT service_role or secret key). Auralis uses the key server-side to proxy Auth requests.
5. Configure strong password requirements, OTP limits, abuse controls, and carefully review email templates.
6. Auralis validates access tokens using the Supabase Auth `GET /auth/v1/user` endpoint on authenticated requests, never by decoding unsigned claims.

## 3. PostgreSQL database

1. Create a managed PostgreSQL instance on Render (https://render.com/docs/postgresql), enable backups and use a paid instance appropriate for real-user retention.
2. Copy its **internal database URL** for the Render web service running in the same region. `DATABASE_URL` must be PostgreSQL, not SQLite.
3. The service creates its own tables on startup (`sessions`, practice, cohort and intelligence tables). The schema is compatible with the database adapter, but migration from existing SQLite needs a **separate and deliberate** step. Do not upload your laptop `.data` or database file to GitHub.
4. Restrict DB access to the web service, ensure SSL where appropriate, and configure scheduled backups. The app's stored-data retention is applied on startup; plan a scheduled job if retention must run continuously.

## 4. Deploy to Render

- Create **New → Web Service**, connect the private GitHub repository.
- Environment: **Python**; use **Python 3.11.9** with `PYTHON_VERSION=3.11.9`.
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/api/health`
- Paid web-service tier recommended. Keep production to **one worker and one instance** until request budgets and state transitions are safe across instances.
- Under Environment, set **secrets privately** (never in code):

  - `AURALIS_DEPLOYMENT_MODE=production`
  - `DATABASE_URL` = Render internal PostgreSQL URL
  - `SUPABASE_URL` = your exact HTTPS Supabase project URL
  - `SUPABASE_PUBLISHABLE_KEY` = project's publishable/anon key
  - `GROQ_API_KEY` = your own private key
  - `GROQ_MODEL=openai/gpt-oss-120b`
  - `AURALIS_PUBLIC_URL` = actual final HTTPS address, without trailing slash
  - `AURALIS_RETENTION_DAYS=30` or your documented policy
  - `AURALIS_MAX_CALLS_PER_MINUTE=15`, `AURALIS_MAX_CALLS_PER_HOUR=90` (starter global limits; monitor provider quota)
  - `AURALIS_EXTRA_HOSTS` = trusted custom domain(s), if applicable

`RENDER_EXTERNAL_HOSTNAME` is provided automatically. Host header allowlisting remains active.

## 5. Real-user acceptance checklist (must be done before launch)

1. `/api/health` responds with `status: ok`. Test sign-up, email confirmation, sign-in, logout, refresh after page reload, and password recovery.
2. With Account A create a session using a real CV you own, consent, Groq 120B, and verify a live generated interview. Inspect provider failures: **no scripted fallback** in hosted mode.
3. Sign in from another device as Account A and check the same saved interview and replay. Restart/redeploy Render and confirm persistence.
4. Create Account B. Confirm B cannot access A's session, dispute notes, college assignments, practice history, exports or delete them, even by guessing A's resource ID.
5. Confirm authentication token expiry, logout, CSRF/CORS behavior, request limits and secret redaction. Verify external links only use trusted hosts.
6. Load-test concurrent saved interviews, restore from a backup, and test DB failure/recovery.
7. Publish a real privacy notice, terms, support contact and retention policy. Verify third-party consent and data deletion (Supabase user deletion requires additional admin-side workflow; local interview data deletion is already available).

## 6. Important limitations

- Password auth uses Supabase, but this is not enterprise identity management. Login, recovery and email delivery depend on your Supabase project configuration and SMTP.
- `GET /auth/v1/user` validates tokens against Supabase over the network. Unavailable Auth service prevents protected requests; this fails closed.
- The existing Auralis interview question, score and retry flows are intact. In hosted mode, Groq failure returns an actionable error; interview answers are saved before generating the next live question and the interview can be resumed.
- Advanced college/invite workflows still use invitation codes and need a dedicated institution-verification and authorization audit before multi-tenant university deployment.
- Local tests cover SQLite and mocked Auth; **a real managed PostgreSQL + Supabase + Groq integration test is mandatory**.
- Process-wide AI call budgeting and some engine concurrency guards are not multi-instance rate limits. Do not scale to multiple workers before moving these to shared transactional controls.
- Actual stored legacy browser-token sessions cannot automatically be tied to new Supabase identities. Start accounts fresh or perform an explicitly reviewed migration with user consent.
- Never advertise automated practice scores as validated hiring or professional-certification outcomes.
