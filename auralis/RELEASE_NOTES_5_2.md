# Auralis 5.2 — Interview Realism Studio

## What shipped

1. **Five interview tracks**: Technical reasoning (default), behavioral examples, case studies, timed challenge, revision/knowledge transfer. All preserve deterministic competency coverage, evidence controls, and question duplicate rejection. Groq / Hugging Face receive explicit model-facing track guidance; scripted demo / local rubric responses have bounded visible prompts. These are settings, not different trained models.
2. **Four interviewer styles**: Supportive, Technical lead, Hiring manager, Panel. Names are textual styles, not real human interviewers. No aggression, protected-trait inference, or hiring suitability decisions.
3. **Question countdown**: Off / 60 / 90 / 120 / 180 seconds. The server stamps question issue time, answer elapsed time, and over-time flag. The per-question countdown is advisory and never discards a late answer. Main session deadline and idempotent request IDs remain unchanged.
4. **Adaptive difficulty toggle**: Passes allowed guidance into the session-scoped question context. This is evidence-constrained model behavior and not an independently verified measure of ability.
5. **Voice delivery notes**: For consented speech capture with a usable transcript, the server calculates approximate transcript words/minute and a small set of common English fillers. Raw audio, audio waveforms, personal traits, voice confidence, and pause timing are not stored or inferred. Transcription and client-reported duration may be inaccurate; scores do not use these notes.
6. **Report and replay**: Include elapsed response time, whether a question limit was exceeded, and a separate unscored speech-delivery note when voice observations exist. The prior 5.1 repair tools, calculation lab, progress history, code provenance, PDF exports and Groq integration are preserved.
7. **Design refinements**: Consistent dark settings section, editorial persona stamp, responsive countdown, readable labels, and dynamic navigation breadcrumb.

## Compatibility

- FastAPI SQLite session snapshots remain backward-compatible, with defaults for missing settings in 5.1 sessions.
- `COPY_OLD_SETTINGS.bat` prefers 5.1 and never overwrites an existing local database.
- Existing Groq/HF credentials are NOT included. Groq API inference cannot be validated without the user's own credential.

## Validation

- 93 Python tests passed, including the existing 5.1 suite and 7 new 5.2 regression tests.
- Browser DOM/layout checks pass at widths 1440, 1024, 768, 390, 360px; no overflow or JavaScript page errors in the controlled fixture.
- FastAPI endpoint `/api/health` starts and reports `5.2.0` on an isolated local port.
- The hosted browser blocks navigation to 127.0.0.1 (`ERR_BLOCKED_BY_ADMINISTRATOR`), so a true browser-to-local-server and Windows microphone/Groq run remain outstanding.

## Boundaries

No real-time audio scoring, conversational audio interruption, automated pronunciation judgement, webcam/proctoring, remote monitoring or verified skill certification is claimed. The app continues to use turn-based voice capture and model-generated practice feedback.
