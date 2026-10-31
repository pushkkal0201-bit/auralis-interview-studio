# Auralis Verification

Run `python -m pytest -q` from the root. Tests cover session lifecycle, owner isolation, provider errors, project evidence, role comparisons, ZIP limits, source paths, source excerpt redaction, Agent Skill loading, mocked Groq credential checks, incident API and X-Ray source citation verification.

Static JavaScript parse check: `node --check app/static/app.js` (optional Node.js command used for development validation; the application runtime needs no Node.js).

Browser checks still required on the user's Windows machine:
1. Run `setup.bat`, then `start.bat` and open the app in Chrome/Edge.
2. Confirm the UI displays Auralis and all five images load.
3. Upload the included ZIP, ensure `bookings.py` appears with source lines.
4. Select an incident, use samples and create a scripted plan, then finish a scripted interview.
5. Click Test live Groq connection after configuring a personal key; if successful, start a new Live AI session.
6. Allow microphone and record a spoken technical answer; check Whisper transcription before submitting.
7. Ask for/observe a source-grounded question in Live AI, view X-Ray and complete an assessment.
8. Verify Skill DNA, JSON export, browser PDF print, retry and deletion.

Unverified here: real API key/model, Windows device TTS/audio quality, public GitHub connectivity, browser E2E automation due to sandbox browser policy.
