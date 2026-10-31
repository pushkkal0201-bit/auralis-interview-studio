# Auralis 5.5 — Campus & Coaching Suite

This update extends the actual Auralis 5.4 FastAPI + SQLite application. Existing routes, interview engine, 5.4 learning plan, voice controls, practical labs, repair studio and PDF exports are retained.

## New workspaces

1. **09 / Placement simulator:** Five ordered stages: aptitude (five deterministic MCQs), restricted-expression coding challenge, facilitated group-discussion rehearsal with opposing viewpoints, technical discussion, and HR behavioral practice. Aptitude and coding are objectively checked against predefined answers / test cases. Last three rounds are stored only as completion metadata and **not auto-scored**. No real campus selection decision or interview outcome is inferred. Max 20 saved simulations per local owner.
2. **10 / Hindi-English coach:** Local English, Hindi and Hinglish response review, a technical glossary for general/software/mechanical/electrical, filler-word observations, response structure prompts, curated parallel phrase examples. No free-text automatic translation, accent, fluency, protected-trait or employability inference. The underlying live interview setup now also accepts a `mixed` language mode. Raw coach text is not stored.
3. **11 / Personal question bank:** Auto-suggests *questions only* when the saved live, completed interview report associates an answer ID with a provisional rubric score <=2/4. Opt-in saves a question card and rotates practice prompts at 1, 3, 7, 14, 30-day intervals. Candidate responses are not stored in the review bank. Spaced practice is not evidence of mastery.
4. **12 / College training portal (LOCAL PILOT):** Teacher-created cohorts, 160-bit one-time invite tokens, pseudonymous student joins, role-specific assignments, self-reported completion, aggregate instructor dashboard, cohort-wide mentor guidance. No teacher access to student CVs, interview transcripts, grades or submitted code. Local owner token is not a verified identity. This is **NOT a secure multiuser, cloud-hosted college SaaS**. Do not expose to a public network or claim production security without genuine authentication, role management, privacy and independent audit.
5. **13 / Assessment reliability lab:** Five reproducible diagnostic fixtures covering mathematical sanity, repeated questions, unsupported credential phrases and inconsistent scores; per-session heuristic audit of question repetition, missing rubric evidence, contradictions and synthetic-data provenance. **Passing the five fixtures does not validate an LLM's grading accuracy, detect all hallucinations or certify an AI system**.

## Data and privacy

- All new records are stored in the same local SQLite database under the existing browser-owner token boundary. No new API keys are included in the ZIP.
- Personal delete-all removes the new simulator runs, question cards, cohort memberships and cohorts, together with existing records.
- Existing `AURALIS_RETENTION_DAYS` also purges expired new records/cohorts at startup; zero disables retention expiry.
- Invitation codes are bearer secrets, revealed once at creation and stored as SHA-256 hashes; they are not identity proofs.
- No source code or free-form campus, bilingual, or question-bank response text is saved.
- Reusing a database copied from Auralis 5.4 adds new tables and columns without dropping existing records.

## Testing

- **136 Python tests passed** after the upgrade, including original 5.4 tests and new owner-isolation, stage-scoring, privacy, scoring-boundary and college-mentor tests.
- JavaScript syntax and Python compilation pass.
- Controlled Chromium fixture tests at 1440, 1024, 768, 390, and 360 px pass for each new screen; important click/form paths were exercised with simulated API responses.
- These fixture screenshots are **not** a live Groq or real multiuser college deployment test. Actual Windows microphone/Groq workflows still require local testing.

## Upgrading

1. Extract the entire ZIP to `D:\Auralis_5_5_Campus_Coaching_Suite`.
2. Stop old Auralis server (`Ctrl+C`).
3. Double-click `COPY_OLD_SETTINGS.bat` and approve copying `.env` / `.data` from 5.4. The script does not overwrite existing destination files.
4. Double-click `START_AURALIS.bat` (first run installs Python dependencies).
5. Open exactly the `http://127.0.0.1:PORT` address shown in CMD. Use `Ctrl+F5` to refresh.
6. Open sidebar destinations 09 through 13; if old cached content appears, perform a hard refresh.

The server intentionally binds to localhost only. Do not substitute `0.0.0.0` merely to enable school access.
