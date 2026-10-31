<!-- Auralis | The Interview Studio -->

<div align="center">
  <a href="https://tinyurl.com/AuralisStudio">
    <img src="docs/media/auralis-hero.gif" alt="Auralis: The Interview Studio. Animated editorial banner illustrating a practice interview." width="100%" />
  </a>

  <h1>auralis.</h1>
  <p><strong>THE INTERVIEW STUDIO</strong></p>
  <p><em>Make the next interview count.</em></p>

  <p>
    A role-aware interview practice workspace that connects preparation, live interviewing, evidence-linked feedback and ongoing progress.
  </p>

  <p>
    <a href="https://tinyurl.com/AuralisStudio"><strong>Launch Auralis</strong></a>
    &nbsp;·&nbsp;
    <a href="#how-to-use-auralis"><strong>Start here</strong></a>
    &nbsp;·&nbsp;
    <a href="#system-architecture"><strong>Architecture</strong></a>
    &nbsp;·&nbsp;
    <a href="#api-reference"><strong>API reference</strong></a>
  </p>

  <p>
    <img alt="Python 3.11" src="https://img.shields.io/badge/Python-3.11-2b4a62?style=flat-square&amp;logo=python&amp;logoColor=white" />
    <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-API-128978?style=flat-square&amp;logo=fastapi&amp;logoColor=white" />
    <img alt="Supabase" src="https://img.shields.io/badge/Supabase-Auth-21594e?style=flat-square&amp;logo=supabase&amp;logoColor=white" />
    <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-Data-345c8b?style=flat-square&amp;logo=postgresql&amp;logoColor=white" />
    <img alt="Groq" src="https://img.shields.io/badge/Groq-Inference-b34d3a?style=flat-square" />
    <img alt="MIT" src="https://img.shields.io/badge/License-MIT-1b3040?style=flat-square" />
  </p>
</div>

> **The practice room is built around the candidate, not a fixed question list.** Auralis uses the role, the candidate's experience and the evolving conversation to structure an interview, then links assessment to the answers that produced it.

---

## Contents

- [The idea](#the-idea)
- [Inside the studio](#inside-the-studio)
- [How to use Auralis](#how-to-use-auralis)
- [System architecture](#system-architecture)
- [Interview lifecycle](#interview-lifecycle)
- [Authentication and data ownership](#authentication-and-data-ownership)
- [Model orchestration and assessment](#model-orchestration-and-assessment)
- [Technology stack](#technology-stack)
- [Repository layout](#repository-layout)
- [Run locally](#run-locally)
- [Cloud configuration](#cloud-configuration)
- [API reference](#api-reference)
- [Data model and persistence](#data-model-and-persistence)
- [Design and product decisions](#design-and-product-decisions)
- [Privacy and data handling](#privacy-and-data-handling)
- [License and credits](#license-and-credits)

## The idea

Interview preparation often separates the things that belong together. A candidate reads a job description in one place, rehearses generic questions somewhere else, then tries to remember what went wrong. Auralis keeps those steps in one workflow.

The interview begins with the candidate's CV and a target job description. From that brief, Auralis organizes competencies and a role-specific scenario. The interviewer then works through the plan, adapting its questions to the answers already submitted. After the session, the assessment connects rubric judgments to specific answer turns, so the candidate can inspect the reasoning behind the feedback rather than relying on a single overall score.

Auralis is designed for students preparing for placements, candidates moving into a new role, engineers practicing technical explanations, and mentors organizing practice routines. The emphasis is on rehearsal, review and repeatable progress, not automated hiring decisions.

## Inside the studio

<p align="center">
  <img src="docs/media/auralis-surfaces.svg" alt="The Auralis workspace connects the interview brief, practice room, evidence-linked assessment and skill evolution." width="100%" />
</p>

These four views form the core of the experience. The supporting tools extend that same cycle into source-code review, engineering scenarios, technical practice and structured learning.


Auralis combines interview preparation with a set of focused practice workspaces.

| Area | What it does |
| --- | --- |
| **The Brief** | Combines CV content, job requirements, role, interview track, language and session preferences into a practice plan. |
| **Practice Room** | Conducts turn-by-turn interviews with typed or spoken answers, follow-up questions, hints and clarifications. |
| **Live Rehearsal** | Reads questions aloud, supports live captions and lets the candidate edit a spoken response before submitting it. |
| **Your Assessment** | Shows competency-level feedback, cited answer passages, replay and the Answer Repair Studio. |
| **Skill Evolution** | Revisits previous sessions and presents assessed competency coverage over time. |
| **Compare Roles** | Builds two interview plans using the same CV against different job descriptions. |
| **CodeProof** | Inspects a small Python source ZIP or public GitHub repository with static AST analysis and file/line references. |
| **Incident Room** | Adds a fixed engineering scenario, including a booking race, slow API or payment retry storm. |
| **Calculation Lab** | Checks engineering arithmetic with explicit formulas, units and assumptions. |
| **Practical Lab** | Offers bounded Python challenges and engineering casework with deterministic checks. |
| **Learning Workspace** | Organizes a four-week study routine from saved interviews and practice attempts; exports a calendar and progress summary. |
| **Campus Placement Simulator** | Rehearses aptitude, coding, group discussion, technical and HR rounds in sequence. |
| **Hindi–English Coach** | Reviews technical terminology and answer structure in English, Hindi and Hinglish. |
| **Personal Question Bank** | Saves selected questions for repeated practice. |
| **College Training Portal** | Supports invitation-based cohorts, assignments and aggregate completion views. |
| **Feedback Quality** | Runs rule-based checks for duplicate questions, citation mismatches and score-evidence inconsistencies. |
| **CV Intelligence** | Matches terms from a job description to passages in a CV. |
| **Technical Whiteboard** | Builds diagrams from labeled components and connections, with local review and an optional consented model review. |
| **Evidence-Linked Grading** | Opens the answer excerpts behind a competency judgment and stores private feedback notes. |
| **Knowledge & Prerequisites** | Maps foundations to applied topics across software, mechanical, electrical and general reasoning. |

### An interview shaped by the role

The brief supports technical, behavioral, case-study, pressure and revision tracks. Candidates can choose an interviewer persona, preferred response language, practice duration and whether to use adaptive difficulty. Questions move through a controlled session rather than appearing as an unrelated sequence of prompts.

### Feedback tied to actual answers

Completed interviews retain the questions, submitted answers, competencies and assessment evidence. A score is connected to recorded answer turns. The replay and repair tools let candidates compare an original answer with a revised one while keeping the rubric visible.

### Engineering practice beyond conversation

The practical areas are deliberately distinct from the language-model interview. The calculation lab evaluates formulas independently. CodeProof parses source without running it. The whiteboard can analyze labeled relationships, and the practical lab records test outcomes. These modules let candidates practice showing their work, not just describing it.

## How to use Auralis

| Prepare | Practice | Review | Improve |
| :--- | :--- | :--- | :--- |
| Define the role and provide context | Work through a structured interview | Explore competencies and answer evidence | Repair answers and revisit progress |


### 1. Open your workspace

Visit **[Auralis Studio](https://tinyurl.com/AuralisStudio)**. Create an account with an email address and password, confirm the email when prompted, and sign in. Returning users can sign in directly. The account also provides session continuity across visits.

### 2. Prepare the interview brief

Open **The Brief** from the navigation. Paste your CV or import a supported document, then add the description of the job you are targeting. Auralis accepts CV/job text and can extract text from PDF, DOCX and TXT documents.

Choose a role and the kind of interview you want to rehearse. You can specify an interview track, interviewer persona, language and duration. For a live interview, select a Groq model and approve the data-processing consent in the interface.

**Example brief**

| Field | Example |
| --- | --- |
| Target role | Backend Software Engineer |
| CV context | Python, REST APIs, PostgreSQL, concurrency and project ownership |
| Job focus | API design, data modeling, debugging and reliable transactions |
| Track | Technical |
| Interviewer persona | Technical lead |
| Language | English |
| Duration | 15 minutes |

### 3. Add project evidence when relevant

The interview can include a small Python source archive or a public GitHub repository through **CodeProof**. It extracts functions, source references and bounded snippets using Python's AST parser. A selected Incident Room scenario can also become part of the interview context.

CodeProof references are attached through server-issued evidence handles, so interview questions can point to inspected source rather than arbitrary filenames supplied by the browser.

### 4. Build the plan and start the interview

Create the plan and review its competencies and scenario. Start the session in **Practice Room**. Each question is tied to a competency in the plan; the current question can also show a concise explanation through **Why this question?**

Answer by typing or using the available microphone controls. You can request a clarification, ask for a hint or skip a question. Spoken responses can be reviewed as text before submission, giving you control over what becomes part of the saved interview.

### 5. Review the assessment

Finish the interview to open **Your Assessment**. Read the competency judgments, supporting excerpts and suggested practice. Use **Print assessment**, **Print full replay** or **Export JSON** when you want a copy of the session.

For a focused second attempt, open **Answer Repair Studio**. Choose an answer, revise it and compare the two responses using the same rubric.

### 6. Build a practice routine

Use **Skill Evolution** for past sessions, **Personal Question Bank** for selected questions and **Learning Workspace** for scheduled practice. The workspace can export its plan as an `.ics` calendar and a private JSON progress summary.

### 7. Explore the specialist workspaces

Use **Compare Roles** when choosing between job directions; **Calculation Lab**, **Practical Lab** and **Technical Whiteboard** for applied technical practice; or **Campus Placement Simulator** for a placement-style sequence. The **Knowledge & Prerequisites** map is useful when a review points to a fundamental topic that deserves another attempt.

## System architecture

<p align="center">
  <img src="docs/media/auralis-architecture.svg" alt="Hosted Auralis architecture connecting the browser, FastAPI application, Supabase Auth, PostgreSQL and Groq." width="100%" />
</p>

The diagram above shows the system boundaries. The detailed dependency flow below maps the components used by the API and interview engine.


The hosted application is a Python FastAPI service serving the browser interface and exposing same-origin JSON endpoints. Supabase handles account identity, PostgreSQL stores application records, and Groq handles consented live model requests. The interview engine stays on the application server, where it manages transitions, validates model output and records session state.

```mermaid
flowchart TB
    U[Candidate / browser]
    UI[HTML · CSS · JavaScript interface]
    API[FastAPI application]
    AUTH[Supabase Auth]
    ENGINE[Interview engine]
    MODULES[Practice and learning modules]
    STORE[Owner-scoped repository layer]
    PG[(PostgreSQL)]
    GROQ[Groq API · GPT-OSS / Whisper]

    U --> UI
    UI -->|HTTPS · same-origin API| API
    API -->|Identity / token verification| AUTH
    API --> ENGINE
    API --> MODULES
    ENGINE -->|Structured model tasks| GROQ
    ENGINE --> STORE
    MODULES --> STORE
    STORE --> PG
    API -->|Optional audio transcription| GROQ
```

**Responsibilities are intentionally separated:**

- **Browser:** Forms, navigation, playback, microphone controls, diagrams, reports and user-approved submissions.
- **API layer:** Request validation, authentication, routing, document intake and response formatting.
- **Interview engine:** Session state, competency selection, question policy, retries, replay and assessment verification.
- **Provider adapter:** Groq API calls, selected model, JSON responses and audio transcription.
- **Persistence layer:** Owner-bound session records, practice history, evidence handles and learning plans.

The locally run edition uses the same core application with **SQLite** for storage. Hosted operation uses **PostgreSQL**, Supabase authentication and Groq for live interviews.

## Interview lifecycle

<div align="center">
  <img src="docs/media/auralis-workflow.gif" alt="Animated Auralis practice workflow from CV and role through interview planning, practice, assessment and saved progress." width="100%" />
</div>


An interview is maintained as a saved session. The system creates an explicit plan, records the submitted answer and generates the next question in the context of that session. A finished session carries its report and remains available through history, export and retry tools.

```mermaid
flowchart TD
    A[CV + job description + preferences] --> B[Validate brief and consent]
    B --> C[Generate structured interview plan]
    C --> D[Save session]
    D --> E[Start interview]
    E --> F[Ask a competency-linked question]
    F --> G{Candidate action}
    G -->|Answer| H[Validate and save answer]
    G -->|Clarify / hint / skip| I[Handle selected action]
    I --> F
    H --> J{Continue session?}
    J -->|Yes| K[Select follow-up or next competency]
    K --> F
    J -->|Finish| L[Generate assessment]
    L --> M[Verify evidence references and rubric]
    M --> N[Save report · replay · repair]
```

The interview engine in `app/engine.py` controls the lifecycle. `app/policy.py` handles question coverage and repetition policy. `app/schemas.py` defines typed input and output contracts. `app/assessment_integrity.py` checks that the model's evidence references correspond to recorded answer turns.

### Model interaction

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant A as FastAPI
    participant E as Interview Engine
    participant G as Groq
    participant D as PostgreSQL

    B->>A: POST /api/sessions
    A->>E: Prepare validated setup
    E->>G: Request plan as structured JSON
    G-->>E: Plan and competencies
    E->>D: Save owner-scoped session
    A-->>B: Session and plan
    B->>A: POST /api/sessions/{id}/start
    A->>E: Start session
    E->>G: Request first question
    G-->>E: Typed decision
    E->>D: Save question and state
    A-->>B: Current question
    B->>A: POST /api/sessions/{id}/actions
    A->>E: Apply answer / action
    E->>D: Record accepted turn
    E->>G: Request follow-up in context
    G-->>E: Next decision
    E->>D: Save updated session
    A-->>B: Next question
    B->>A: POST /api/sessions/{id}/finish
    E->>G: Request competency assessment
    G-->>E: Report with answer references
    E->>E: Validate rubric and evidence
    E->>D: Save final report
    A-->>B: Assessment and replay
```

### Structured decisions, not unbounded responses

Auralis asks the selected model for schema-shaped JSON. Pydantic validates the structure; application checks then reconcile competency IDs, scenario branches and source references against the plan and the inspected evidence already in the session. Assessment references are checked against saved answers before they appear in the report.

The result is a clear division of labor: the model supplies language and reasoning for the interview; the application controls what can be accepted and recorded.

## Authentication and data ownership

Hosted Auralis uses Supabase email authentication. The backend communicates with Supabase Auth through HTTPX and verifies bearer tokens against the user endpoint. Application records are associated with a derived owner identifier based on the verified account ID.

```mermaid
sequenceDiagram
    autonumber
    participant U as Browser
    participant A as Auralis API
    participant S as Supabase Auth
    participant P as PostgreSQL

    U->>A: Email + password
    A->>S: Authenticate credentials
    S-->>A: Access and refresh tokens
    A-->>U: Access token + HttpOnly refresh cookie
    U->>A: Request private resource with Bearer token
    A->>S: Verify account identity
    S-->>A: Verified user ID
    A->>P: Query record using derived owner ID
    P-->>A: Matching account record
    A-->>U: Private workspace response
    U->>A: POST /api/auth/refresh with cookie
    A->>S: Rotate refresh token
    S-->>A: Updated session tokens
    A-->>U: New access token + refresh cookie
```

The access token is held in browser memory; the refresh token is placed in a secure, HttpOnly cookie in hosted mode. Application session lookups and mutations include the owner's identifier. Account operations include signup, login, email recovery, password update, refresh and logout.

## Model orchestration and assessment

**Groq inference.** The hosted service uses Groq for GPT-OSS model requests. `app/provider.py` sends structured plan, question, assessment and retry tasks to Groq's chat-completions API. The provider uses JSON response mode, with the returned payload checked against the corresponding Pydantic model. The configured hosted model is `openai/gpt-oss-120b`.

**Speech.** Browser speech synthesis reads questions aloud. Spoken answers can be transcribed using browser recognition or Groq's Whisper transcription endpoint, depending on the selected interaction. The candidate reviews the resulting text before sending it as an answer. Optional camera preview remains on the device; video frames are not uploaded by Auralis.

**Assessment integrity.** The model proposes a report against the plan's competency rubric. Auralis checks the set of competency identifiers and the referenced answer-turn IDs. The report displays evidence excerpts, competency status, practice notes and score context. Unassessed competencies are kept distinct from scored ones.

**Question selection.** Session policy tracks which competencies have been addressed and considers previous answers when choosing follow-ups. Interview tracks, persona and language are preserved in session context.

**Project-grounded questions.** CodeProof uses Python `ast.parse` to inspect source code as data. It extracts bounded references and does not run uploaded repository code. The interview can then use approved source references to ask about implementation decisions.

## Technology stack

| Layer | Technology | Why it is used |
| --- | --- | --- |
| Interface | HTML5, CSS3, vanilla JavaScript | Same-origin browser experience with no separate frontend build server. |
| Typography | Bodoni Moda, DM Sans, IBM Plex Mono | Editorial headlines, clear interface copy and readable technical details. |
| Application API | Python 3.11, FastAPI, Uvicorn | Typed HTTP endpoints and an async-capable Python service. |
| Validation | Pydantic v2 | Explicit constraints for inputs, plans, decisions and reports. |
| Identity | Supabase Auth | Email-based accounts, verified identities, recovery and refresh sessions. |
| Cloud persistence | PostgreSQL via psycopg 3 | Durable account-owned sessions and practice records. |
| Local persistence | SQLite | Lightweight local development and offline practice data. |
| Model inference | Groq + GPT-OSS | Live interview planning, follow-ups, assessments and retries. |
| Speech transcription | Groq Whisper / browser speech APIs | Converts spoken responses to reviewable text. |
| HTTP client | HTTPX | Server-to-provider requests with timeout and error handling. |
| Documents | pypdf, python-docx, python-multipart | CV and job-document extraction and uploads. |
| Source inspection | Python AST and ZIP validation | Non-executing Python project analysis with file/line references. |
| Deployment | Render + Blueprint YAML | Git-connected Python hosting and environment configuration. |
| Automation | GitHub Actions + pytest | Source checks and automated application tests on repository changes. |

No GPU, Docker container or Node.js server is required to run the application itself.

## Repository layout

The deployed repository keeps application source under `auralis/`:

```text
.
├── README.md                     # GitHub project overview
└── auralis/
    ├── app/
    │   ├── main.py               # FastAPI routes, middleware and app setup
    │   ├── auth57.py             # Supabase authentication adapter
    │   ├── auth_abuse.py         # Authentication request budgets
    │   ├── database.py           # SQLite / PostgreSQL adapter
    │   ├── store.py              # Session and owner-scoped persistence
    │   ├── engine.py             # Interview lifecycle and orchestration
    │   ├── policy.py             # Question and competency policy
    │   ├── provider.py           # Groq model and transcription adapter
    │   ├── schemas.py            # Pydantic contracts
    │   ├── assessment_integrity.py
    │   ├── documents.py          # Document parsing
    │   ├── codeproof.py          # Static source inspection
    │   ├── incidents.py          # Engineering incident scenarios
    │   ├── learning_workspace.py # Plans, calendar and summaries
    │   ├── career_suite.py       # Placement, question bank and college modules
    │   ├── intelligence56.py     # Matching, whiteboard and evidence tools
    │   └── static/               # Browser UI, styles and assets
    ├── skills/
    │   └── adaptive-interviewer/ # Interview skill and rubric references
    ├── scripts/                  # Diagnostics, data and operations utilities
    ├── tests/                    # Backend and feature tests
    ├── examples/                 # Sample CVs, roles and project evidence
    ├── docs/                     # Architecture and engineering documentation
    ├── requirements.txt
    ├── render.yaml
    ├── .env.example
    ├── setup.bat
    ├── start.bat
    └── LICENSE
```

## Run locally

### Windows quick start

Install **Python 3.11** and Git. From a local clone of the repository:

```cmd
cd auralis
setup.bat
start.bat
```

Open the localhost address printed by the launcher in Chrome or Edge. The launcher chooses an available port if the default is already in use.

The local edition can be explored with the included sample brief and scripted practice mode. To use a live model, configure a Groq API key in your private local environment. The `configure-groq.bat` launcher is available for that setup.

### Manual Python setup

```powershell
cd auralis
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. The local application uses SQLite in its `.data/` directory. The `.env` file holds local configuration and is excluded from version control.

### Run the automated checks

From the `auralis` directory:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

A GitHub Actions workflow definition for Python tests and JavaScript syntax checks is included at `auralis/.github/workflows/tests.yml`.

## Cloud configuration

The hosted service uses the `staging` branch and the Blueprint at `auralis/render.yaml`, with `auralis` as its Render root directory.

| Render setting | Value |
| --- | --- |
| Runtime | Python 3.11 |
| Root directory | `auralis` |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check | `/api/ready` |

Configuration is supplied through Render environment variables, not committed credentials:

```dotenv
AURALIS_DEPLOYMENT_MODE=production
AURALIS_PUBLIC_URL=https://YOUR-SERVICE.onrender.com
AURALIS_EXTRA_HOSTS=YOUR-SERVICE.onrender.com
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_PUBLISHABLE_KEY=YOUR_PUBLISHABLE_KEY
GROQ_API_KEY=YOUR_GROQ_API_KEY
GROQ_MODEL=openai/gpt-oss-120b
AURALIS_RETENTION_DAYS=30
```

`AURALIS_PUBLIC_URL` is the canonical HTTPS origin used in password recovery. `AURALIS_EXTRA_HOSTS` adds explicit trusted hostnames. Supabase's **Authentication → URL Configuration** should contain that origin in its Site URL and redirect allowlist. The Groq key and database credentials remain on the server.

Two health endpoints serve different purposes: `/api/health` reports application liveness, while `/api/ready` checks database availability.

## API reference

The browser uses the same FastAPI service as the public UI. In hosted mode, private routes use a Supabase bearer token. The routes below are selected from `app/main.py`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/public-config` | Frontend authentication and hosted-mode configuration. |
| `POST` | `/api/auth/signup` | Create account. |
| `POST` | `/api/auth/login` | Sign in and establish refresh cookie. |
| `POST` | `/api/auth/refresh` | Refresh account session. |
| `POST` | `/api/auth/logout` | Sign out. |
| `POST` | `/api/auth/recover` | Request recovery email. |
| `POST` | `/api/auth/password` | Set password with authenticated recovery session. |
| `GET` | `/api/health` | Service liveness. |
| `GET` | `/api/ready` | Database readiness. |
| `POST` | `/api/documents` | Extract document text. |
| `POST` | `/api/codeproof/zip` | Inspect bounded Python source archive. |
| `POST` | `/api/codeproof/github` | Inspect supported public GitHub repository. |
| `GET` | `/api/incidents` | List synthetic practice incidents. |
| `POST` | `/api/sessions` | Create an interview plan and session. |
| `GET` | `/api/sessions` | List signed-in user's sessions. |
| `GET` | `/api/sessions/{id}` | Retrieve a session. |
| `POST` | `/api/sessions/{id}/start` | Start interview. |
| `POST` | `/api/sessions/{id}/actions` | Submit answer, hint, clarification or skip. |
| `POST` | `/api/sessions/{id}/finish` | Generate final assessment. |
| `POST` | `/api/sessions/{id}/retry` | Begin answer repair or parallel retry. |
| `GET` | `/api/sessions/{id}/export` | Export session JSON. |
| `POST` | `/api/transcribe/{id}` | Transcribe consented audio. |
| `GET` | `/api/learning/progress` | Summarize saved skill evidence. |
| `GET` | `/api/workspace` | Open learning workspace. |
| `POST` | `/api/workspace/plan` | Create a practice plan. |
| `GET` | `/api/workspace/calendar.ics` | Export practice calendar. |
| `POST` | `/api/practical/code` | Evaluate a bounded coding task. |
| `POST` | `/api/practical/engineering` | Evaluate engineering casework. |
| `POST` | `/api/intelligence/match` | Compare CV content with job requirements. |
| `POST` | `/api/intelligence/whiteboard/review` | Review structured diagram locally. |
| `GET` | `/api/intelligence/evidence/{id}` | Retrieve assessment evidence. |
| `POST` | `/api/privacy/delete-all` | Delete account-owned Auralis records. |

### Example: create an interview session

The request uses the same schema as the browser's interview setup. The bearer token comes from a signed-in account.

```bash
curl -X POST "https://YOUR-SERVICE.onrender.com/api/sessions" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cv": "Backend engineer with Python, PostgreSQL, API design and transactional booking projects.",
    "jd": "Design reliable backend APIs, data models and transaction-safe services.",
    "role": "Backend Software Engineer",
    "provider": "groq",
    "ai_model": "openai/gpt-oss-120b",
    "consent": true,
    "interview_track": "technical",
    "language": "en",
    "duration_minutes": 15
  }'
```

The returned session identifier is used by the subsequent `/start`, `/actions` and `/finish` endpoints. Each action includes the current question ID and a client-generated request ID, keeping the submitted turn associated with the correct question.

## Data model and persistence

Auralis uses relational tables for ownership and activity metadata, with structured JSON session payloads for the interview state.

| Table or group | Contents |
| --- | --- |
| `sessions` | Interview ID, owner, revision and serialized session state. |
| `source_evidence` | Owner-linked CodeProof inspection results and evidence handles. |
| `practice_attempts` | Practical exercise identifiers, timestamps and test counts. |
| `learning_plans` | The current saved practice plan per account. |
| `review_cards` | Saved personal question-bank cards. |
| `placement_simulations` | Campus placement rehearsal records. |
| `college_cohorts`, `college_members`, `college_assignments`, `college_completions` | Cohort membership, assignments and completion metadata. |
| `intelligence_disputes`, `intelligence_practice` | Assessment review notes and topic-practice records. |
| `ai_usage`, `auth_attempts` | Shared model-use and authentication request budgets. |

Session updates use a revision check so a write is associated with the version it loaded. Record access is scoped by the account-derived owner identifier rather than by a browser-supplied session ID alone.

## Design and product decisions

### One service for the browser and API

FastAPI serves the static browser application and the JSON API from the same origin. It keeps deployment and session handling straightforward while allowing the frontend to remain framework-light.

### Separate authentication from application records

Supabase establishes who the user is. The Auralis database stores what that user has practiced. The API validates the account identity and resolves ownership before reading or updating a record.

### Keep model output behind typed boundaries

The interview provider is an adapter, not the authority for session state. A model response must satisfy Pydantic's contract and the application's competency and evidence checks before it becomes part of the saved conversation.

### Preserve the original answer

A candidate's first response remains available alongside its repair attempt. That makes improvement visible as a comparison between actual submissions, not a rewritten transcript.

### Use deterministic tools where the task calls for them

Arithmetic checking, source parsing, rule-based CV matching and bounded coding exercises use explicit program logic. Model inference is used for open-ended interviewing, coaching and selected consented reviews.

### Treat each user action as part of an owned session

Auralis carries the verified account identity through session and learning routes. Request IDs, expected question IDs and revision checks support consistent turn handling and saved progress.

## Privacy and data handling

Auralis is an account-based practice environment. Its hosted records include interview content, selected source evidence, assessments, practice history and saved learning plans. Live interview content is sent to Groq when the candidate explicitly consents in the interface; the provider key stays server-side.

The application supports deleting saved Auralis records and exporting session data. Session exports omit the original CV and job-description fields by default. The interview interface treats model feedback as practice feedback, not an employment decision or an independent verification of the candidate's claims.

For source-code exercises, upload only code you have permission to share and keep credentials out of repositories and archives. The local `.env` and database directories are excluded from version control.

## License and credits

Auralis is developed by **Team Synergy**. The repository contains work credited to RoleReady contributors and Team Synergy, under the **MIT License**. See [LICENSE](auralis/LICENSE) and [third-party notices](auralis/THIRD_PARTY_NOTICES.md) for source attribution and dependency licensing.

---

<div align="center">

**auralis.** · **THE INTERVIEW STUDIO**

*Make the next interview count.*

[**Launch the studio**](https://tinyurl.com/AuralisStudio) · [**Return to top**](#auralis)

</div>
