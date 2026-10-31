# Auralis 5.4 — Personal Learning Workspace

## New capabilities
- **08 / Learning workspace**: editorial, keyboard-friendly interface for setting weekly practice frequency and time budget.
- **Four-week deterministic study plans** with flexible focus (balanced, interview, Python coding, engineering), 2–7 days per week and 15–120 minutes per day.
- **Evidence-grounded suggestions**: only completed, non-demo, non-provisional AI rubric scores and saved practice attempt metadata are used as weak signals. No fabricated scores.
- **Manual practice tracking**: planned/completed/skipped task states persisted in SQLite, by browser-owner key.
- **Summary statistics**: scheduled sessions, completions, practice minutes, prior interviews, coding/engineering attempts.
- **Practice calendar (.ics)** and **private progress summary (.json)** export; user-initiated only.
- **Privacy**: plan data is deleted by existing Delete All privacy action; the same session-retention policy expires old plans. Plans do not include candidate CV, job text, transcripts or code.

## API
- `GET /api/workspace`: plan, aggregated progress and limitations.
- `POST /api/workspace/plan`: generate or replace a four-week plan.
- `PATCH /api/workspace/plans/{plan_id}/tasks/{task_id}`: mark an activity planned/completed/skipped.
- `DELETE /api/workspace/plan`: delete only the plan.
- `GET /api/workspace/calendar.ics`: owner-scoped all-day calendar export.
- `GET /api/workspace/summary.json`: owner-scoped, redacted progress export.

## Non-goals and limitations
No account sync, cloud notifications, real-time reminders, automatic grading of checklist completions, validated competency measurement, or actual Google/Outlook Calendar connection. Existing Skill DNA remains model-graded and provisional. Current activity streak is calculated from manual completion dates and is not a measure of competence. Imported calendar copies do not update automatically when tasks change.

## Validation
130 FastAPI/Python regression tests passed, including 5.4 privacy, inputs, multi-owner scope, calendar export, and existing 5.3 functionality. Browser fixture checked 1440/1024/768/390/360 viewport widths with synthetic API responses; not live Groq inference. Run live features on your own device.
