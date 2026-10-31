# Auralis 5.1 — Learning Studio

## What changed

### Answer Repair Studio

- A dedicated panel now appears at the start of a completed assessment.
- Pick any recorded answer, read its competency rubric and model feedback, then compare the initial answer against the latest saved retry.
- Reuses the existing persisted `retry` and `retry_history` endpoints. No historical records need migration.
- The original submission is retained, and unavailable AI grading remains explicitly unscored.
- A score-gap explanation is shown when the previous assessment provides one.

### Technical Calculation Lab

- `POST /api/technical/check` checks four bounded formula families: gravitational load, bend allowance, ideal plate bending stiffness ratio, and balanced three-phase current.
- Optional user-supplied answer comparison displays arithmetic difference, not certification.
- Requires the same owner token as the rest of the application.
- No arbitrary expression evaluation, user code execution, solver, or deployment-dependent numerical model.
- Important limitations and assumptions are displayed with every result.

### Skill DNA Evolution

- `GET /api/learning/progress` derives trends from stored completed, non-demo, non-provisional model assessments.
- Only explicit, valid rubric scores are shown. No new grade is inferred from question coverage, retry content, or time spent.
- Per-competency grouping uses exact normalized names; two different names are not merged speculatively.
- Retains score, session, timestamp, role and provider provenance for each chart point.
- Uses local owner isolation and the existing data retention/deletion policy.
- Only the last 100 stored sessions and up to 20 chart points per competency are visualized.

## Compatibility

- Backend version is `5.1.0` and all previous session routes remain available.
- Existing Studio 4/3.4 SQLite database and API key configuration may be copied to the new folder with the server stopped.
- Old record formats continue to load; older absent score-gap data remains marked as unspecified.
- No new Python dependencies.

## Known limits and test scope

- AI scores are unverified practice feedback and may not be comparable across differently structured interviews.
- Only four formula families are currently supported; formulas do not prove safety, material adequacy or standards compliance.
- Live Groq/Hugging Face requests require local API credentials and consent. No real model inference was run here.
- Automated Python tests and static Chromium DOM/responsiveness checks were run; direct browser network navigation to the local server was blocked in this execution environment.
