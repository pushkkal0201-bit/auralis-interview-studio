# Auralis 3.1: Reliable Local Interview Operations

**Release intent:** industry-oriented *local practice prototype*. Not certified/validated for employment screening, not authenticated multi-user SaaS, and not tested against production availability requirements. A live API token and provider access are still required for genuine AI inference and graded reports.

## Improvements from the user's timed AI/ML interview

1. **Coverage-first control:** `app/policy.py` determines the required competency. Each competency gets up to two attempts before the controller rotates to untested skills, and it rotates earlier when time is running low. This is enforced server-side, not just written in a prompt.
2. **Duplicate rejection:** Exact duplicate questions are rejected across the session. Similar rephrasings are rejected within the same competency. At most one repair call is made before a local rubric question is used.
3. **Quota/network fallback:** After an AI-generated plan exists, failures during question generation result in a **visibly labeled local rubric question**. The candidate's submitted answer and previous interview evidence remain saved. The original model and provider are unchanged. There is **no paid inference fallback** and the local fallback is never described as real AI generation.
4. **No fabricated assessments:** If the model fails at report time, the application provides a **PROVISIONAL OFFLINE REPORT** with evidence and deliberately **no scores**. Clicking *Retry AI assessment* retries the same live provider when available.
5. **Rubric scoring integrity:** The model must distinguish `incorrect_reasoning` (0/4 with cited answer evidence), fragmentary/partial knowledge (1–2), sound reasoning (3–4), insufficient evidence (unscored), and not assessed (unscored). Contradictory reports are rejected and repaired once; on repeated failure the report is explicitly provisional. The assessment remains an AI opinion, not a verified skill measurement.
6. **Evidence and limitations:** The report provides answer-linked quotes, status, low/medium/high confidence, coverage count, untested competencies, fallback log, and limitations. Long answer excerpts are disclosed; no code execution is claimed.
7. **Time-aware completion:** The controller avoids generating a new question if fewer than 35 seconds remain after an answer. Interview data stays available to finish and generate the report.
8. **Privacy:** Local SQLite is retained for 30 days by default (`AURALIS_RETENTION_DAYS=30`, checked on startup); set to `0` to disable auto-purge. History includes *Delete all my interview sessions* scoped to the browser workspace. Manual `backup-data.bat` creates a PRIVATE local database backup outside Git tracking; deletion does not delete manual backups.
9. **Windows port resilience:** `start.bat` chooses an available loopback port from 8000-8009 and prints the exact URL if an older instance is occupying port 8000. `AURALIS_PORT` overrides the preferred port.

## Windows installation

Extract new ZIP to a **new folder**, open `auralis`, then run:

```cmd
setup.bat
configure-groq.bat
start.bat
```

Use a real Groq key (`gsk_...`) from https://console.groq.com/keys. No secret is included in this release; do not paste your secret into an issue, chat or screenshot. Keep your existing `.env` private.

For migration, **stop the original v3.0 server** and copy the original `.env` and `.data` directory into the new `auralis` folder. To avoid unintentional cleanup of older sessions when you launch, set `AURALIS_RETENTION_DAYS=0` in `.env` before starting, or run `backup-data.bat` against the old folder first. The new build keeps the old session JSON structure readable.

Auralis now automatically chooses a free port if 8000 is busy. **Open the exact URL printed in the console**, not the old bookmarked URL. On startup, run `curl http://127.0.0.1:8000/api/health`, using the actual port printed by the new server.

## Real test case

1. Select **Live GPT-OSS · Groq Cloud** and **GPT-OSS 120B**. Accept consent.
2. Use the fictional AI/ML resume and JD and generate a live plan.
3. Intentionally make two wrong statements about Pandas imputation.
4. Confirm the questions move from the first competency to another instead of cycling indefinitely.
5. Let time expire, click *Finish & assess*. The report should show `0/4 · incorrect reasoning` for an actually assessed, substantively wrong answer, if the model can reliably support that evaluation. Unasked competencies must remain `Not assessed`.
6. If Groq is unavailable when generating a question, a banner **LOCAL RUBRIC FALLBACK** must be shown. If unavailable at report generation, **PROVISIONAL OFFLINE REPORT** appears and all scores are withheld; retry report when service returns.
7. Export JSON, print/save feedback, delete a session, check history. For voice, test both browser speech recognition and Groq Whisper independently.

Run checks from the `auralis` directory:

```cmd
.venv\Scripts\python.exe -m pytest -q
curl http://127.0.0.1:8000/api/health
```

## Security and reliability boundaries

**Included:** local loopback server, workspace token, per-session ownership checks, strict request/response schema validation, origin and host restrictions, request size caps, content security policy, source-only AST inspection (never execute uploaded code), SQLite revision checks, answer idempotency, provider timeout/rate-limit error handling, consent before cloud calls, redacted provider errors, export and deletion.

**Not included:** verified professional/psychometric interview scoring, verified interviewer fairness or bias audit, real multi-tenant login, HTTPS public hosting, organizational RBAC, encrypted backups, formal service-level guarantees, automated CI/CD, centralized monitoring, penetration testing, disaster recovery, or independent security/privacy audit. Do **not** deploy it to the public Internet or use scores as hiring decisions without addressing these.

## Recovery paths

| Condition | Behavior |
|---|---|
| 8000 already in use | Start on next available 127.0.0.1 port; printed in CMD. |
| Groq/HF quota during plan | Show error; no fake plan. Retry later or consciously choose Scripted demo. |
| Groq/HF quota during question | Local, labeled rubric question; transcript is committed. |
| Model chooses wrong competency/repeats | One repair attempt; then transparent rubric fallback. |
| Groq/HF quota or malformed report | Unscored provisional evidence report; retry grading later. |
| Microphone permissions/unsupported voice | Typed answers remain available. |
| Time expires | No new answers; *Finish & assess* stays available. |
| Database corrupted or lost | Restore a locally created database backup while server is stopped. |

