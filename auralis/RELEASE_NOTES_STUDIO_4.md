# Auralis 3.4 — Studio 4 / Interface and Information Architecture

## Changed
- Replaced generic illustrative hero with a **capture from the real interview UI running in scripted demonstration mode**; sample data is explicitly marked illustrative.
- Rewrote homepage in direct product-specific language; removed promotional AI decorations, card stacks, and unnecessary visual elements.
- Added a three-part editorial walkthrough with asymmetric rhythm and typographic separation.
- Staggered CV and role entry, distinct pace controls, discoverable collapsed advanced tools, and consolidated consent/submit step.
- Refreshed interview room, answer entry, X-Ray, skill evidence, assessments, comparison, history and empty states in a common restrained visual system.
- Replaced the previous screen CSS cascade with a single self-contained `studio.css`; retained `style.css` only for print to protect 3.3 assessment / replay layout.
- Corrected CSP to permit the two Google Fonts asset origins. No external scripts are permitted.
- Retained every existing interaction ID and API route, improved navigation accessibility, and added a setup shortcut from empty interview room.
- Advanced tools remain in the DOM and functional; opening is user-controlled using native `details`.

## Compatibility
- Existing local SQLite session records remain compatible; no DB migration is required.
- The installed Groq/HF `.env` configuration is re-usable by copying locally.
- No API keys or user interview database are included in the ZIP.
- Backend interviews and assessment grading are unchanged from v3.3; this is an interface refinement, not a new validated scoring model.

## Remaining manual checks on the user's PC
- Live Groq inference and account-specific quota, voice/microphone permissions, final print output on Windows Chrome, and native offline font fallback.
