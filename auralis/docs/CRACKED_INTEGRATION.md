# Cracked × Auralis: integration status

The goal is to bring Cracked's entire placement-preparation suite into Auralis without breaking Auralis's existing interview engine or misrepresenting model-only guidance as an executed workflow.

## Upstream and licensing

Cracked by Nishant Tiwari: https://github.com/nishant-Tiwari24/cracked

Source at import: main branch, November 11, 2026 (release v1.3.0).
Cracked's skills and supporting files are vendored in vendor/cracked/skills.
The upstream MIT license is preserved in vendor/cracked/LICENSE. Altered or deployed features must continue to respect the attribution and copyright notice.

## What this branch adds

- All 19 skill definitions and their bundled reference files/scripts, stored separately from Auralis application code.
- A validated catalog in app/cracked_suite.py with an explicit per-feature integration status.
- A bounded AI-guidance adapter using the existing Groq provider, explicit consent and account-scoped rate budgets.
- An opt-in wrapper app.cracked_entry:app exposing GET /api/cracked/features and POST /api/cracked/coach.
- A standalone authenticated /cracked interface with searchable-by-category skill selection and a guided response.
- Tests for catalog integrity, mandatory consent, response provenance and skill name allowlisting.

**Not implemented:** complete parity with Cracked's CLI/agent-based workflows. They have external tool dependencies and cannot be made functional by embedding prompts alone. Guided responses explicitly state which facts were not checked. The existing Auralis interview system is unchanged.

## Local start (new entry point only)

From the auralis/ directory:

    python -m pip install -r requirements.txt
    python -m uvicorn app.cracked_entry:app --host 127.0.0.1 --port 8000

Open http://127.0.0.1:8000/ once to initialize a local workspace, then open
http://127.0.0.1:8000/cracked.

The new entry point is opt-in. The existing app.main:app and production deployment configurations are not modified. Do not switch a production deployment until the tests, login/refresh behavior, and retention controls have been verified in staging.

The guided AI response requires a configured GROQ_API_KEY and explicit consent.
Input is sent to Groq only on submission; there is no new persistent user-profile store.

## Coverage by skill

| Original skill | Auralis entry point | Real parity |
| --- | --- | --- |
| setup-cracked | The Brief | Related native workflow; Cracked CLI setup not run |
| cracked-profile | Skill Evolution | Related native data; Cracked local journal not imported |
| company-intel | Career Skills guided panel | Not fetched or verified in guidance mode |
| mock-interview | Practice Room | Related native interviews; no Cracked random differential grader |
| oa-sim | Placement Simulator, Practical Lab | Bounded practice only; no full multi-language OA judge |
| pattern-coach | Career Skills guided panel | Model-led Socratic coaching |
| core-viva | Practice Room | Related native questions; not equivalent to SQL execution |
| system-design-mock | Interview Whiteboard, Practice Room | Related native workflows |
| hr-round | Practice Room | Related native behavioral track |
| defend-my-project | CodeProof | Python static inspection only; does not execute repositories |
| roast-my-resume | Career Skills guided panel | Text-based review, not actual ATS vendor evaluation |
| resume-blueprint | Career Skills guided panel | Guided draft, not authenticated resume file edits |
| jd-match | CV Match | Related native keyword matching |
| github-glowup | Career Skills guided panel | Does not fetch/review actual GitHub accounts |
| make-it-hireable | Career Skills guided panel | Recommendations only; no repository mutations |
| referral-dm | Career Skills guided panel | Drafting only; no messages sent |
| prep-plan | Learning Workspace | Related native study planning |
| rejection-review | Career Skills guided panel | Needs verified interview history context |
| offer-decode | Career Skills guided panel | Qualitative only; no tax calculations from prompt |

## Requirements for full parity

1. Company Intelligence: authoritative source URLs, dated external-data fetches, resilient caching, rate-limit handling and offline disclaimers.
2. Verified coding judge: isolated per-language execution, CPU/memory/time caps, no network access, randomized differential test sets, independent reference solutions and abuse monitoring. Never execute user-submitted code in the FastAPI server process.
3. Persistent profile, journal and weak-spot analytics: tenant-scoped database records, user deletion, retention, export and provenance for every score.
4. DSA, OA, viva and system-design session controllers: timers, hidden grader state, assessment rubrics and verifiable outcomes.
5. Resume and GitHub tools: user-supplied documents and authorized repository access, source-grounded observations, privacy and explicit approval before edits.
6. Referrals and offers: factual input validation, no sending without explicit approval, source-year verification before presenting tax estimates, safe scenario comparisons.
7. Cross-feature integration: connect company research → prep plan → interview → grader → review → next plan, reusing Auralis account ownership and existing session APIs.
8. Reproducible deployment and evaluation: CI tests across OSes and model providers, threat modeling, a staging rollout, checks for hallucinated tool usage, and independent repeated evaluations.

## Verification

Run from auralis/:

    python -m pytest tests/test_cracked_suite.py -q
    python -m pytest tests -q

The branch has not yet been runtime-tested in a live Auralis deployment. Until tests complete successfully and remaining adapters are implemented, label the work an **integration foundation**, not "all Cracked features fully working."
