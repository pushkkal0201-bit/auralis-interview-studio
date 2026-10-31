# Auralis 5.7.2 private staging readiness: test evidence

Date: **2026-10-31**. Artifact based on the uploaded `Auralis_5_7_2_Security_Hardening(2).zip`.

## What was actually executed locally

| Item | Result | Method |
|---|---|---|
| Original project suite | **PASS: 171 passed, 1 skipped** | `pytest -q --disable-warnings` on supplied archive |
| Extended local project suite | **PASS: 175 passed, 1 skipped** | Same command, after adding four offline regression tests |
| A/B owner-scoped sessions | **PASS** | Synthetic verified Supabase principals, request denial for cross-owner GET, export, start, finish, delete, plus persistence after app recreation |
| Local SQLite backup and restoration | **PASS** | Copied SQLite database to isolated path, restored expected synthetic record, verified owner isolation |
| Tool script syntax | **PASS** | Python compileall of both new scripts |
| Cloud environment preflight | **BLOCKED by missing configuration** | `python -m scripts.cloud_preflight`, intentionally did not reach network |
| Real Supabase signup/login/recovery | **NOT EXECUTED** | No Supabase staging project/account access |
| Real managed PostgreSQL schema/transactions | **NOT EXECUTED** | Requires isolated test DB URL and `psycopg` |
| Real Groq model inference | **NOT EXECUTED** | No private provider key; no billable requests made |
| Live A/B API isolation | **NOT EXECUTED** | No protected deployed staging URL and two verified account credentials |
| Real PostgreSQL backup-restoration | **NOT EXECUTED** | No managed backup/restore databases provided |
| Hosting deployment and access gate | **NOT EXECUTED** | No connected Render/GitHub deployment permissions; blueprint is a deployment template only |

The single skipped test is `tests/test_postgresql_real_optional.py`, gated by both a separate disposable PostgreSQL URL and explicit confirmation.

**Environment caveat:** local Python 3.13.5 and existing environment packages were used. The pinned production dependency versions and Render Python 3.11.9 build were **not** independently installed and verified here. CI/Render builds must run before acceptance sign-off.

## Added assets

- `render.yaml`: Render staging web service declaration; **does not make hosting private by itself**.
- `STAGING_ACCEPTANCE.md`: access-control setup and real sign-off runbook.
- `scripts/staging_acceptance.py`: opt-in two-account HTTPS test with controlled synthetic records and optional billable Groq interview plan.
- `scripts/verify_restored_database.py`: read-only specified-session validation on an independently restored PostgreSQL instance.
- `tests/test_staging_readiness_local.py`: extra local isolation, restart, SQLite backup/restore, and safety-gate tests.

**Release decision:** Not approved for real users; private staging and actual integration evidence remain outstanding.
