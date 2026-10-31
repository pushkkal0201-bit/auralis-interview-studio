# Auralis 5.7.2: private staging runbook

**Status of this package:** prepared locally, not deployed. Nothing here claims a real service passed acceptance. Use test-only credentials and synthetic data. No user CVs.

## 0. Lock down access BEFORE starting the web service

A private GitHub repository does not make a Render web service private. The `render.yaml` declares a **public web service** by default. Do not deploy it until you have enforced and tested an access gate, such as:

* An HTTPS custom domain protected by an identity-aware gateway (e.g. Cloudflare Access) **plus disabling direct `onrender.com` access**, and no alternative bypass path; or
* Render inbound IP rules where available under your plan, restricted to your approved testing IPs.

Render `Protected` projects/environments do not by themselves restrict their public web endpoints. Supabase email/password login is application account isolation, **not** a substitute for gating the staging origin. Require HTTPS. Block unwanted crawlers at the edge; don't rely solely on `robots.txt`. Make sure gateway authentication is compatible with the application's `Authorization: Bearer` tokens. If the gate changes Host/Origin, verify the actual values before enabling traffic.

## 1. Provision independent staging resources

1. Private GitHub repo: push the **inner `auralis/` folder** to a `staging` branch. Review `.gitignore`; no `.env`, DB exports, cookies or secrets.
2. Separate Supabase staging project with email verification and private SMTP test inboxes. Turn **off public signups** after you create/verify exactly two disposable test users A and B, and any explicitly allowlisted instructor. Configure recovery redirects to the exact staging HTTPS origin.
3. Separate managed PostgreSQL database with backups/PITR enabled. Restrict external database connectivity; use internal `DATABASE_URL` from the web service.
4. Separate Groq key or strict provider-level spending cap, plus `GROQ_MODEL` set to a listed/available supported model. Limit costs.
5. Configure hosting service from `render.yaml`. `AURALIS_PUBLIC_URL` must exactly match the HTTPS origin visible to the browser. If it is a custom domain, add that hostname to `AURALIS_EXTRA_HOSTS` (no URL scheme or wildcard). Do not point staging to production services or customer accounts. Create a separate daily retention job running `python -m scripts.retention_maintenance` with the same DB URL.
6. Confirm with a browser **not** in your testing group that staging returns an access-denied response *before* app content or API is reachable.

## 2. Validate environment and real cloud dependencies

On the server or another secure machine with authorized access and dependencies installed:

```bash
python -m scripts.cloud_preflight
python -m scripts.cloud_preflight --live
python -m scripts.cloud_preflight --live --inference
```

`--inference` consumes Groq quota. This checks an actual Groq model response; the Supabase Auth health endpoint is NOT a login/signup/recovery test.

## 3. Two real Supabase accounts, actual PostgreSQL-backed records

Set these **as private environment variables**, not in `.env` committed to Git or shell history. Use two accounts verified in Supabase first:

```text
AURALIS_STAGING_URL=https://staging.example.com
AURALIS_TEST_ISOLATED_STAGING=I_CONFIRM_DISPOSABLE
AURALIS_STAGING_GATE_VERIFIED=I_VERIFIED_ACCESS_GATE
AURALIS_TEST_A_EMAIL=<verified_disposable_account_a>
AURALIS_TEST_A_PASSWORD=<private_value>
AURALIS_TEST_B_EMAIL=<verified_disposable_account_b>
AURALIS_TEST_B_PASSWORD=<private_value>
```

If using Cloudflare Access service-token authentication for automated tests, also set `CF_ACCESS_CLIENT_ID` and `CF_ACCESS_CLIENT_SECRET` privately. The harness sends them in their dedicated headers alongside the Auralis account Bearer tokens. For IP-allowlisted staging, neither token is needed. Check the HTTPS access gate independently before setting the confirmation flag.

Then execute (only after your private gateway is configured):

```bash
python -m scripts.staging_acceptance
python -m scripts.staging_acceptance --live-session
```

Expected: exact-HTTPS Origin enforcement; real A/B Supabase login, token refresh, cookie flags, separation of question-bank records, unauthorized edits/deletes, cohort-creation denial for B, real Groq plan in hosted mode (opt-in), PostgreSQL session persistence, cross-account GET/export/delete/start/finish denied, and cleanup. Log output omits identities, keys, tokens, CV content and HTTP error response bodies. It assumes a direct trusted authorized connection; a separate access gateway may require an approved service-token or logged-in browser session first.

Additional **human-verified** tests still required: actual signup email delivery, password reset email and callback, token expiry, full multi-turn interview/report, device-to-device reload, disconnect/reconnect behavior, concurrent worker budget enforcement, logged-out UI, consent, SMTP, account closure (disposable only), and deletion of only the intended account. Do not record a pass without screenshots/log evidence from real staging.

## 4. Real PostgreSQL smoke test (dedicated, disposable test DB)

**DO NOT set `AURALIS_TEST_DATABASE_URL` to a database storing user/customer data.** The optional test creates tables and data.

```text
AURALIS_TEST_DATABASE_URL=<separate throwaway postgresql URL>
AURALIS_TEST_ISOLATED_DATABASE=I_CONFIRM_DISPOSABLE
```

```bash
python -m pytest tests/test_postgresql_real_optional.py -q
```

This is a smoke test, not a full migration, concurrency or failover certification.

## 5. Actual backup and restoration, not merely an export

1. Create a synthetic tagged test interview/session using a disposable test user. Save its ID privately as `AURALIS_RESTORE_EXPECTED_SESSION_ID`.
2. Use your paid Render Postgres **Recovery** page to create a logical export or PITR point after the test record exists.
3. Restore to a **new independent database instance**, never to the active database. For logical export, follow the vendor's `pg_restore` guide on a confirmed-empty restore target; it can drop objects. With PITR, Render creates a separate instance.
4. From a machine allowed to reach both databases, configure:

```text
DATABASE_URL=<original staging DB URL>
AURALIS_RESTORED_DATABASE_URL=<distinct restored DB URL>
AURALIS_RESTORE_EXPECTED_SESSION_ID=<known pre-backup test session ID>
AURALIS_RESTORE_VALIDATION=I_CONFIRM_READ_ONLY
```

```bash
python -m scripts.verify_restored_database
```

The verifier is read-only; it compares the SHA-256 of **one specified session's owner and payload** in the source and restored databases, then ensures the two database endpoints differ. It does not test complete backup integrity or delete/restore anything.

5. Do full recovery acceptance separately: schema/table counts, sample records from both accounts, permissions, point-in-time accuracy, encrypted export storage, retention, restoration logs, database connectivity, and documented RPO/RTO. Capture screenshots or an auditable report. Delete only approved disposable recovery infrastructure after verification.

References: [Render recovery docs](https://render.com/docs/postgresql-backups), [Render Blueprint access rules](https://render.com/docs/blueprint-spec), [Supabase Auth settings](https://supabase.com/docs/guides/auth/general-configuration).

## 6. Go/no-go checklist

- [ ] Protected staging origin proven inaccessible to unauthorized visitors
- [ ] Staging-only Supabase project; verified A/B identities and recovery email test
- [ ] Staging-only managed PostgreSQL ready; migrations and readiness checked
- [ ] Groq model listing AND one real inference succeeded
- [ ] A/B account, mutation, export and session isolation succeeded
- [ ] Auth/cookie behavior and expired tokens validated in real browser
- [ ] Real backup restored to a SEPARATE database and its records validated
- [ ] Service restart, concurrent traffic and provider outage/recovery validated
- [ ] Provider quotas, audit logs, retention job, WAF and incident plan verified
- [ ] Evidence recorded and approved before any real user invitation
