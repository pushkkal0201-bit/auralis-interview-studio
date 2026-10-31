# Auralis 5.7.1 | Production deployment and acceptance guide

This is a source-code release, **not a deployed service or security certification**. The local tests cannot access your private Supabase, Render/PostgreSQL or Groq accounts. Finish the acceptance plan below before using real student data or inviting customers.

## A. What has been fixed

- Server-verified Supabase user ownership, short-lived access token in memory, and HttpOnly refresh cookie (introduced in 5.7).
- Cloud PostgreSQL persistence with revision-checked interview saves (introduced in 5.7).
- Strict hosted live Groq interviews and recovery after a failed follow-up (introduced in 5.7).
- **5.7.1:** shared PostgreSQL model-call counters for each verified account *and* globally, using a transaction-level lock. Multiple workers cannot trivially reset usage counters. This is a usage-safety control, **not billing/fraud prevention**.
- **5.7.1:** only explicitly approved Supabase user UUIDs can create a hosted college cohort or assign/mentor. Authenticated students may join using an invite code. This is a controlled pilot, **not verified institutional affiliation**.
- **5.7.1:** `/api/ready` tests database availability and returns HTTP 503 if unavailable. `/api/health` is process liveness only.
- **5.7.1:** optional self-service account closure, with fresh-password confirmation and a server-only Supabase admin key; disabled if the key is not configured.
- **5.7.1:** production privacy wording, safer setup diagnostics, and regression tests.

## B. Prepare GitHub from Windows

1. Install Git for Windows and Python 3.11.9. Extract ZIP to `D:\Auralis_5_7_1_Production_Hardening` (or any known directory).
2. The GitHub repository root must be the inner `auralis` folder containing `app/`, `requirements.txt`, and `scripts/`.
3. Check `.gitignore`. **Never stage** `.env`, `.data`, `.venv`, SQLite/WAL files, private keys, student CVs, or backups.
4. Create a **private** GitHub repository and push the extracted source.

   ```cmd
   cd /d "D:\Auralis_5_7_1_Production_Hardening\auralis"
   git init
   git add .
   git status --short
   git commit -m "Auralis production hardening"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/auralis-interview-studio.git
   git push -u origin main
   ```

## C. Configure Supabase Auth

1. Create a Supabase project at https://supabase.com/dashboard.
2. Enable email/password authentication **with email confirmation**. Set up a reliable outbound SMTP provider and real sender domain for verification and recovery.
3. Configure **Authentication → URL Configuration** with the final Render HTTPS site URL and the permitted password-reset redirect address. Review strong password settings and email signup limits.
4. Copy the **Project URL** and **publishable/anon key**. Keep them in Render environment variables; Auralis uses them server-side.
5. Sign up an instructor account, confirm its email, and copy the instructor's **Supabase Auth UUID** from Authentication → Users. If you want instructors to create cohorts, put only verified instructor UUIDs in `AURALIS_COLLEGE_INSTRUCTOR_IDS` (comma-separated). Without an allowlist, hosted cohort creation returns 403.
6. **Optional self-service account closure:** provide a server-only legacy `service_role` key as `SUPABASE_SERVICE_ROLE_KEY` in Render. It has powerful administrative privileges. Never place it in JavaScript or GitHub. If you do not configure it, users can delete their Auralis records, and must contact you to remove the Supabase Auth identity manually from the dashboard. Test the account deletion flow with a disposable account first.

## D. Create managed PostgreSQL and verify backups

1. Create a **paid, managed Render PostgreSQL** database in the same region as the web service, with backups/recovery enabled. Use the internal database URL from Render for `DATABASE_URL`.
2. Keep the database isolated from public networks except where access is required. Auralis creates necessary tables on startup. The first deployment should use a **new empty database**.
3. Use the **Render Recovery** page to confirm point-in-time recovery and exports. Perform a restoration into a separate disposable database and verify records. Do **not** restore into a live database with user records.
4. For PostgreSQL integration tests, create a **separate disposable test database**, set:
   - `AURALIS_TEST_DATABASE_URL` to the test database connection URL.
   - `AURALIS_TEST_ISOLATED_DATABASE=I_CONFIRM_DISPOSABLE`.
   - Run `python -m pytest tests/test_postgresql_real_optional.py -q`.

   This test is skipped unless both settings are supplied. **Do not use the real customer database.**

5. Local SQLite interview history is **not** automatically linked to Supabase accounts. Do not upload `.data/` into hosted PostgreSQL without a consented identity mapping and reviewed migration.

Current Render backup documentation: https://render.com/docs/postgresql-backups

## E. Create the Render web service

Connect the **private** GitHub repository using https://dashboard.render.com/.

| Setting | Value |
|---|---|
| Service type | Web Service, Python |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health-check path | `/api/ready` |
| Python | `PYTHON_VERSION=3.11.9` |
| Instance | Paid tier for retained real-user service |
| Workers | Start with **one worker and one web instance** while verifying session concurrency and recovery |

Set these environment variables in Render, never Git:

```text
AURALIS_DEPLOYMENT_MODE=production
AURALIS_PUBLIC_URL=https://YOUR-EXACT-SERVICE.onrender.com
DATABASE_URL=<PRIVATE_MANAGED_POSTGRESQL_URL>
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_PUBLISHABLE_KEY=<PUBLISHABLE_KEY>
GROQ_API_KEY=<PRIVATE_GROQ_KEY>
GROQ_MODEL=openai/gpt-oss-120b
AURALIS_RETENTION_DAYS=30
AURALIS_MAX_CALLS_PER_MINUTE=15
AURALIS_MAX_CALLS_PER_HOUR=90
AURALIS_GLOBAL_CALLS_PER_MINUTE=60
AURALIS_GLOBAL_CALLS_PER_HOUR=500
AURALIS_COLLEGE_INSTRUCTOR_IDS=<OPTIONAL_VERIFIED_INSTRUCTOR_UUIDS>
SUPABASE_SERVICE_ROLE_KEY=<OPTIONAL_SERVER_ONLY_ADMIN_KEY>
```

`RENDER_EXTERNAL_HOSTNAME` is supplied by Render. For additional custom domains, set `AURALIS_EXTRA_HOSTS` to a comma-separated allowlist of **trusted hostnames**. Never use `*`. Domain configuration and reverse proxy must enforce HTTPS. Do not enable multiple instances until concurrency, rate limiting, and DB failure recovery have been tested against real infrastructure.

## F. Preflight and real inference test

From the configured Render environment or a secure machine that can reach the database:

```bash
python -m scripts.cloud_preflight
python -m scripts.cloud_preflight --live
python -m scripts.cloud_preflight --live --inference
```

The first command checks environment variable presence without network requests. The second checks PostgreSQL, Supabase Auth health, and Groq model listing. The third makes **one real Groq inference** and may use provider quota. The script intentionally prints no passwords or keys. Supabase Auth health does **not** prove email signup/login/recovery works.

## G. Mandatory real-user acceptance test (requires your accounts)

- [ ] Create **two separate verified Supabase accounts** and one optional instructor account.
- [ ] Confirm email verification, password recovery, login, logout, refresh across page reload, and an expired-token refusal.
- [ ] As Account A upload a CV you own, consent to Groq data processing, start a real interview, answer questions, finish, save a report, and revisit it from another browser/device.
- [ ] Verify real GPT-OSS inference via `scripts.cloud_preflight --live --inference`. No scripted fallback in hosted interview mode.
- [ ] As Account B attempt GET, modify, export, dispute, and delete A's resources using A's IDs: all must fail.
- [ ] Try Account B creating/managing a college cohort: expected **403** unless B's Auth UUID is explicitly allowlisted.
- [ ] Test 429 response after exceeding a verified account's configured AI call budget; after recovery, existing interview progress must remain.
- [ ] Restart/redeploy the web service; saved records must persist in PostgreSQL.
- [ ] Simulate a brief database outage in a **test deployment**; `/api/ready` must become 503 and recover after DB connectivity returns.
- [ ] Test account-data deletion and (if configured) full account closure with a **disposable account**, including verification that Account B's data remains.
- [ ] Restore an encrypted backup into a separate instance and compare selected test records. Exercise password/key rotation.
- [ ] Load-test several concurrent accounts and interrupted Groq requests; inspect errors and latency, not just a healthy homepage.
- [ ] Publish a genuine privacy notice, terms, data-retention policy, customer support address, and third-party Groq processing disclosure; have them legally reviewed for your jurisdiction.

## H. Remaining limitations, even after 5.7.1

- No remote Supabase/PostgreSQL/Groq integration was performed during packaging because your private credentials and managed service are not available here.
- The instructor allowlist controls who can **administer** cohorts. It does not prove ownership of a real university. Do not market institutional verification without additional vetting.
- Account deletion spans two services (Auralis database and Supabase Auth) and is **not an atomic cross-system transaction**. If Supabase deletion fails after deleting the Auralis data, the Auth identity may remain: the user can retry and support must reconcile the account.
- On-demand database connections are not pooled or optimized for heavy traffic. PostgreSQL failover, high concurrency, latency, and backups require real-cloud testing.
- Retention pruning runs on application startup, not an independent scheduled cron service. Set up regular deployment/cron maintenance in production if strict retention deadlines are promised.
- Shared AI limits are application-side safety caps, **not** a payment, anti-abuse, or contractual quota system. Add payment provider accounting and external edge rate limiting before selling plans.
- The college portal is a guided pilot, not institution-vetted multi-tenant LMS. Assessment scores are provisional coaching judgments, never validated hiring decisions.
- This release is not a guarantee of security, legal compliance or availability. You need an external security review and full acceptance testing before a public customer launch.
