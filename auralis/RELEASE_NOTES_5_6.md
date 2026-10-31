# Auralis 5.6 — Intelligence & Evidence Studio

This release extends **Auralis 5.5** with five owner-scoped/local-first modules. It does not replace the original interview engine.

## Functional changes
1. Browser voice-first interview room with optional camera preview, interruptible playback, interim captions and reviewed answer submission through existing `/api/sessions/.../actions`.
2. `/api/intelligence/match` lexical job/CV evidence matching; explicit self-reported claim labeling, no bogus numeric suitability score. Save unmatched role criteria to existing Question Bank.
3. `/api/intelligence/whiteboard/review` deterministic labeled graph inspection. `/api/intelligence/whiteboard/ai` consent-gated Groq feedback on labeled nodes/edges with bounded size and no freehand image submission. UI supports drag, connections, pen and PNG export.
4. `/api/intelligence/evidence/{sid}` raw turn-linked excerpts, existing rubric scores, explicit next-score gap; `/api/intelligence/disputes/{sid}` saves owner-scoped notes. Competency score labels on the report now open the evidence screen.
5. `/api/intelligence/knowledge/{domain}` curated prerequisites and rotated practice prompts, including low-score interview signals. `/api/intelligence/knowledge/practice` records private self-report metadata without modifying Skill DNA.

## Storage and privacy
- New tables `intelligence_disputes`, `intelligence_practice`. Existing DB schema remains compatible. No CV/JD, diagram, camera, or audio recording saved by the new modules.
- New tables cleaned by privacy delete-all and retention cleanup; score disputes for individual sessions deleted when sessions are deleted.
- Existing bearer browser workspace token is **not** enterprise authentication.
- Avoid claiming full duplex audio or true image-based whiteboard analysis: this is turn-by-turn audio with live captions, and optional AI on explicitly labeled graph structure.

## Tests
- Python regression suite: 143 pass, including seven dedicated 5.6 API tests and existing features.
- JavaScript syntax checks passed.
- Controlled Chromium fixture at 1440, 1024, 768, 390, 360 px; actual FastAPI endpoints called via test-driver forwarding, no horizontal overflow or browser JS exceptions; diagram PNG download verified.
- Local FastAPI health/version checked 5.6.0. No personal Groq credentials used, no live inference or physical microphone/camera verified.
