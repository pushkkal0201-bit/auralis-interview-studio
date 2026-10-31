# Premium edition verification

- Python: `python -m pytest -q` — 73 passed (one existing Starlette/httpx deprecation warning).
- JavaScript: app.js and premium.js passed `node --check`.
- DOM compatibility: all 92 original IDs retained; no duplicate IDs.
- Chromium browser workflow: sample setup, plan, answer, clarification, assessment, retry, history and deletion passed.
- Three browser regressions passed: pending microphone cancellation, stale recording cancellation and session isolation. These use a mocked microphone.
- Layout checked at 1440, 1024, 768, 390 and 320 CSS px: no document horizontal overflow; bundled Manrope loaded.
- Reduced-motion waveform disabled, demo shortcut populated fields, active-navigation ARIA state updated; no page JavaScript errors in the layout run.
- Desktop and phone screenshots inspected. Remaining legacy blue CodeProof surfaces corrected.
- Print fixture with twelve long answers: concise report 4 pages; full replay 11 pages. Full replay contains Question 12 and Interview X-Ray; no raw bold-markdown markers. Both generated through Chromium using the complete served application.
- Smoke harness updated to expand the existing replay disclosure before accessing its retry action. Print harness updated to use the served application, so all styles and scripts are included.

The static Impeccable detector identified undersized labels (raised to 11px) and reported legacy color rules/white-background assumptions that do not describe the active screen cascade. Its output is not treated as an accessibility certification.

Limits: live provider inference, real microphone hardware, Safari/Firefox and native Windows batch launch were not exercised in this environment. No credentials were requested or used. This is a local project deliverable, not a hosted deployment.
