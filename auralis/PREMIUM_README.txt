AURALIS / EDITORIAL PRACTICE STUDIO (Auralis 3.3 foundation)

The redesigned website is a complete Python FastAPI app, not a static HTML mockup.
Art direction is defined in DESIGN.md and DESIGN_SYSTEM_EDITORIAL.md.

COLORS: Archive paper #F1EEE5, deep ink #242B26, field olive #6E795D.
TYPE: Bodoni Moda + DM Sans + IBM Plex Mono through Google Fonts, with
Windows/system fallbacks if the device is offline. No font binaries are bundled.

GET STARTED
1. Extract ZIP into D:\Auralis_Editorial_Studio\auralis.
2. Stop the old Auralis process with Ctrl+C.
3. Open cmd in the new auralis folder.
4. Copy the old .env and .data from your existing Premium Edition.
5. Run setup.bat then start.bat.
6. Open the exact http://127.0.0.1:<port> printed by the terminal.
7. Press Ctrl+F5 to clear previous cached CSS.

All source/server API contracts and the report printing implementation remain
from Auralis 3.3. Run python -m pytest -q for regression tests.
No live external model inference was performed during visual QA.
