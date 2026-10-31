# Auralis Editorial Practice Studio / Premium redesign

This is a visual redesign of the user-supplied Auralis Premium Edition on the Auralis 3.3 application foundation, not a separately rebuilt interview engine.

## Rebuilt
- Responsive editorial homepage with custom typographic question vignette and accurate product messaging
- Three-color paper/ink/olive art direction; no purple-blue or radial gradients, neon glows or generic feature-card grids
- Bodoni Moda / DM Sans / IBM Plex Mono typography via optional web-font stylesheet and offline system fallbacks
- Numbered, clear text navigation, custom mobile layout, asymmetric CV + job description brief
- Unified visual theme for interview, report, role comparison, history, optional CodeProof and incident practice
- Accessibility-focused controls, native inputs, keyboard-visible focus, reduced-motion compatibility

## Preserved
- FastAPI server, API providers, Groq model and consent configuration, local SQLite history, privacy controls
- 95 existing HTML element IDs and script contracts
- User-owned `.env` and `.data` migration paths; new ZIP never includes secrets or user interviews
- Working v3.3 report/replay/print implementation unchanged

## Validation
- 77 backend and design tests passed, JavaScript syntax passed
- Chromium tested 1440, 1024, 390 viewport widths with no horizontal overflow
- In mocked local browser environment: sample CV fills correctly, navigation switches views and creates no JS errors
- Fonts might use fallback on offline devices; font binary files are not included
- External Groq inference and actual microphone capture require verification on the user's computer

## Upgrading from Premium Edition
Stop old server; extract this ZIP to a NEW directory; copy `.env` and `.data` from the prior local Premium Edition; run `setup.bat` and then `start.bat`. Refresh browser cache with Ctrl+F5 and use the exact port printed in CMD.
