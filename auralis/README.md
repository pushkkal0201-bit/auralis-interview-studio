# Auralis 5.7.2 | Cloudflare-method Security Hardening

See `SECURITY_REVIEW_5_7_2.md` and `DEPLOY_5_7_2.md` for the focused security review, deployment controls, and remaining cloud validation requirements.

# Auralis 5.7.1 | Production Hardening

**Start here:** [Production deployment and acceptance guide](DEPLOY_5_7_1.md) or [Windows local start](README_5_7_FIRST.md).

5.7.1 hardens the 5.7 foundation with shared rate limits, institutional permissions, account deletion, and readiness checks. 5.7 introduced real Supabase-authenticated user accounts, PostgreSQL connection support,
strict Groq interviews and safer recovery when the live provider temporarily fails.
The rest of the application is preserved for existing development and practice workflows.

---

# AURALIS 5.5 — Campus & Coaching Suite

**Team Synergy** · Local-first AI interview practice studio. Built on FastAPI, SQLite and browser JavaScript; optional GPT-OSS inference through Groq or Hugging Face.

**New in 5.5:** Campus Placement Simulator, Hindi-English Coach, Personal Question Bank, College Training Portal (local pilot), and Assessment Reliability Lab. Read [`RELEASE_NOTES_5_5.md`](RELEASE_NOTES_5_5.md) for exact behavior, privacy boundaries, limitations and test evidence. Previous features from 5.1–5.4 remain available. This release is **not** production-certified for student accounts or automated hiring decisions.

## 1. Windows quick start (no Node.js / Docker / GPU)

1. Install **Python 3.11 or 3.13** (avoid Python 3.15 beta) and enable "Add Python to PATH" during setup.
2. Extract the ZIP to a regular folder (for example `C:\Auralis`).
3. Double-click **`setup.bat`**. Python creates `.venv` and installs dependencies.
4. Double-click **`start.bat`** and keep the terminal open.
5. Open the exact **http://127.0.0.1:PORT** URL printed by the launcher in Chrome or Edge (normally 8000; it automatically chooses 8001+ when occupied).
6. Select **Scripted demo**, click **Use sample CV & job**, **Build interview plan**, and **Start interview**.
7. For the signature demo, upload `examples/auralis_codeproof_demo.zip` into **CodeProof** before creating the interview plan. Choose *Last-slot race condition* in **Incident Room**.

The scripted demo uses predefined questions, and **must not be presented as real live AI**. It deliberately does not generate ability scores.

## 2. Enable LIVE Groq AI

1. Create a Groq account and create your own Groq API key at **https://console.groq.com/keys**.
2. After `setup.bat`, double-click **`configure-groq.bat`**. Paste the key into its hidden prompt. The key is stored in your local `.env`, which Git ignores. **Never paste the key into chat, a GitHub commit, a screen recording or a public screenshot.**
3. Restart **`start.bat`**.
4. Click **Test selected real GPT-OSS model** in the interface. This checks your key and the configured model without claiming a completed interview inference test.
5. Choose **Live AI**, accept Groq data-processing consent, upload a *synthetic* CV / job description, and build a new plan. Record an answer or type, then finish and check the evidence-linked assessment.

The default `.env.example` contains:

```dotenv
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b
```

Groq free-tier limits and model availability may change. Check live connectivity before presenting. The in-app model selector overrides the default `GROQ_MODEL` for each new interview. Models must be enabled for your Groq account and support JSON responses. The product does **not** claim to run GPT-OSS locally or to use Gemma 4.

### PowerShell alternative

```powershell
cd C:\path\to\auralis
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

For a manual key setup, edit the copied `.env` locally with Notepad. Do not commit it. `start.bat` is bound to `127.0.0.1` deliberately. This is not yet hardened for public Internet hosting.

## 3. Features and honest boundaries

| Capability | Implementation | Important limitation |
|---|---|---|
| CV / job mapping | Upload PDF/DOCX/TXT; live AI plans role-specific competencies | Claims are not proof of ability |
| Voice conversation | Browser speech synthesis and Groq Whisper audio transcription | Turn-based, requires browser microphone + network |
| Adaptive follow-ups | Session engine + GPT-OSS JSON decisions | Generated questions can still be wrong |
| CodeProof | Static Python `ast` extraction, bounded ZIP, public GitHub importer, file/line citations | Does not execute code or verify safety/authorship |
| Interview X-Ray | Decision type, competency, model-facing rationale, cited source excerpt | Explanations are not privileged model chain-of-thought |
| Incident Room | Three repeatable synthetic scenarios | Fixtures, not real telemetry; live model chooses discussion |
| Skill DNA | Visualize rubric outcomes and not-assessed skills | No scores in scripted demo |
| Agent Skill | `skills/adaptive-interviewer/SKILL.md` + references loaded by Groq provider | It is a reusable instruction skill, not a third-party harness modification |
| Replay, repair, retry | Save exact answers, compare efforts with same rubric | Not a certification of competence |
| Storage & export | Owner-scoped SQLite, JSON export, browser print-to-PDF | Single-machine local storage, not encrypted |

### CodeProof usage

Use a **small source-only Python ZIP** (max 4 MB compressed, 1.6 MB uncompressed, maximum 45 Python source files) or a valid **public** GitHub URL (`https://github.com/owner/repo`). GitHub imports need connectivity and small repositories. Uploaded code is parsed with Python `ast` and **never executed**. Auralis shows bounded source references with filenames and line ranges; static indicators do not prove a vulnerability. Source-code comments and candidate documents are **untrusted data**. Never upload `.env`, private credentials, private production code, or third-party code without permission.

### Incident Room

Choose a synthetic incident on the setup screen; its facts and fake logs become labeled source context for the live interview. The three exercises are:
- **Last-slot race condition**: concurrent booking requests.
- **Slow API**: high database queries per request.
- **Payment retry storm**: duplicate side effects during retries.

The scripted demo cannot dynamically adapt to these incidents. Select **Live AI** to test context-aware probing.

## 4. Repo structure

```text
app/
  main.py              FastAPI routes, upload limits, local-only security
  codeproof.py         Original, non-executing AST code inspector
  incidents.py         Reproducible synthetic incident fixtures
  skill_loader.py      Agent Skill frontmatter and reference loading
  engine.py            Interview state, x-ray decision traces, evidence verification
  provider.py          Groq GPT-OSS JSON calls and Whisper transcription
  demo.py              Honest scripted offline demo
  documents.py         PDF/DOCX/TXT extraction
  schemas.py           Pydantic request and response contracts
  store.py             SQLite session snapshots
  static/              Browser interface, JS speech and product imagery
skills/adaptive-interviewer/  Agent Skill Open Standard SKILL.md & references
examples/            Fictional resume/job data, synthetic Python source ZIP
tests/               Core and feature regression tests
docs/                Architecture and legacy background documentation
```

## 5. Automated tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The extended suite includes security and function checks for malicious ZIP paths, oversized archives, secret-like assignments, no-code-execution inspection, fake Groq connectivity, source-grounded X-Ray decisions, provider failure rollback, session isolation and interview state transitions.

## 6. Hackathon 2-minute live demo walkthrough

1. **CV + Job (20 seconds):** Use the synthetic samples, choose Live AI after verifying Groq.
2. **CodeProof (20 seconds):** Upload the included demo ZIP. Expand `bookings.py` and show actual file-line references.
3. **Incident Room (10 seconds):** Choose Last-slot race condition and display the fake logs.
4. **Voice interview (45 seconds):** Ask and answer one technical question. Show an adaptive follow-up about atomicity; if the model doesn't raise it, ask a different answer, don't present a scripted prompt as dynamic.
5. **X-Ray (15 seconds):** Open the source evidence and why-question panel.
6. **Assessment (10+ seconds):** Finish and show Skill DNA and evidence-linked scoring. A short interview may leave many skills explicitly unassessed.

**No invented performance gains, no recruiting/hiring decisions, no facial/emotional profiling.** Model-generated evaluation is subjective practice feedback. In a no-key demo, show the scripted flow, CodeProof inspector and code-linked evidence honestly.

## 7. Security & privacy

- Only run `start.bat` on localhost. This single-user prototype is not public multi-tenant SaaS.
- The app uses a local browser workspace token to scope SQLite sessions. Local data is **not encrypted**.
- Candidate CVs, job descriptions, selected code excerpts, transcripts and scores are persisted locally to SQLite. Delete a session from Session History to remove its row.
- Live mode sends relevant CV/JD/excerpts/answers to Groq. Audio is sent for Whisper transcription. Check Groq's current data terms before submitting real personal data.
- Do not include `.env`, SQLite files, secrets, logs, private resumes or real job applicant audio in a public repository.
- Public GitHub import requests are restricted to `github.com` and `codeload.github.com`, with strict path validation and bounded responses.

## 8. Team and license

**Team:** Synergy  
**Team lead:** Pushkkal Gupta  
**Hackathon product:** Auralis  
**Source license:** MIT (third-party technologies retain their respective licenses). Read `THIRD_PARTY_NOTICES.md` for dependency and model attributions.

The original **Auralis 3.0** extended the RoleReady prototype; Auralis 3.3 adds evaluation and export reliability. The build has automated tests and local functionality; final live-provider and actual microphone demonstrations must be tested with your credentials and device before submission.


## Open-weight model selector (Groq and Hugging Face)

Auralis uses **one Groq API key** with three eligible downloadable-weight models.
In Interview Setup, choose:

- `openai/gpt-oss-20b` — default fast interviewer (Apache 2.0).
- `openai/gpt-oss-120b` — deeper reasoning (Apache 2.0).
- `qwen/qwen3.8-27b` — optional preview model (Apache 2.0); may disappear/change.

Choose **Live AI**, confirm consent, then select a model and click **Test selected real GPT-OSS model**.
Every session saves its selected model; ongoing sessions do not change when you change the selector for future sessions.
Role comparisons and targeted retry use that selected model as well.
Groq hosts inference remotely: the model weights are open, but the Groq hosting service is not itself an open-source runtime.
The Qwen model remains preview-only on Groq, so don't rely on it for a critical demo.
The API key stays on the backend in `.env`; never put it in `app.js` or commit `.env`.
The UI does not call OpenAI API or xAI Grok API.

Model availability, account limits, and pricing can change; verify at https://console.groq.com/docs/models .


## 9. Real GPT-OSS on Hugging Face (NEW in v3.0)

**This is a genuine API integration, not simulated inference.** The Hugging Face provider sends prompts over HTTPS to `https://router.huggingface.co/v1/chat/completions`, checks provider responses, and validates every plan/question/report with the existing Pydantic schemas. There is no automatic switch to a scripted response when a paid/remote model fails.

### Enable hosted GPT-OSS without a GPU

1. Go to https://huggingface.co/settings/tokens and create a token that can call Inference Providers. Check current inference credits at https://huggingface.co/settings/billing.
2. Run **`configure-hf.bat`** in the project folder. Paste your token privately; `.env` is Git-ignored.
3. Run **`start.bat`**, open `http://127.0.0.1:8000`, choose **Live GPT-OSS · Hugging Face** under **Intelligence**, and select one of:
   - `openai/gpt-oss-120b:fireworks-ai` (recommended for structured JSON assessments)
   - `openai/gpt-oss-20b:groq` (routed through Hugging Face)
4. Tick the data-sharing consent checkbox. Click **Test selected real GPT-OSS model**. Unlike the Groq model-list test, the Hugging Face test makes one actual short model completion call. This may consume inference credits.
5. Start a new interview using the sample CV and job. In Hugging Face mode, you can answer by typing or with browser speech recognition (which may send speech to the browser vendor).

### Optional: Continue using Groq

Run `configure-groq.bat` for Groq-hosted GPT-OSS and Groq Whisper transcription. Groq and Hugging Face can be configured independently. You do not need an OpenAI API key or xAI Grok key. Both deliver *open-weight* model inference; their hosting infrastructure is not open source.

### API and security details

- `/api/open-models`: returns allowlisted models grouped by inference provider.
- `/api/live/check?provider=huggingface&model=openai%2Fgpt-oss-120b%3Afireworks-ai`: performs a short real inference probe.
- `app/huggingface_provider.py`: HF transport, timeout/error handling, JSON schema mode, model validation and no-secret errors.
- `app/engine.py`: every interview and retry retains its selected provider and model.
- Auralis continues to bind to `127.0.0.1`. This is a local hackathon prototype, not a public multi-user production deployment.
- **Provider credits, rate limits and structured-output support can change.** Test the exact model with your token before the live presentation. No direct account test was possible during packaging because no user API credentials were available.

### Upgrade from v2.1 without losing your data

Extract v3.0 into a **new directory**, and run `setup.bat` with Python 3.11. Your prior v2.1 files remain unchanged. To carry over historical sessions and settings, copy your **private** `.env` and `.data` folder into the new project folder on your own machine while its server is stopped. Do not upload those files to anyone, include them in public GitHub, or share tokens in chat.

### Test status

Run `test.bat` or `python -m pytest -q`. The added tests cover Hugging Face HTTP request construction, structured outputs, invalid outputs, provider isolation, missing credentials, rate limits, consent, and the interview controller with an **injected mock** (not a live-cloud benchmark).

**Reference documentation**:
- https://huggingface.co/docs/inference-providers/en/guides/gpt-oss
- https://huggingface.co/docs/inference-providers/index
- https://console.groq.com/docs/models
- https://help.openai.com/en/articles/11870455-openai-open-weight-models-gpt-oss

## Version 3.2 — Assessment integrity and scoped security hardening

This release improves the 3.1 evaluation failures exposed by an electrical-engineering test report. It preserves the Windows Python 3.11 / FastAPI / Groq / Hugging Face stack and local SQLite sessions. Key additions: more representative grading evidence, question X-Ray based on actual controller state, explicit multi-answer score trajectories, guards for known contradictory electrical judgments, owner-bound server-verified CodeProof citations, source snippet redaction, local model request budgets, labeled outage fallbacks for plans/questions/grades/retries/comparisons and concise report printing.

See [`docs/RELIABILITY_3_2.md`](docs/RELIABILITY_3_2.md), [`docs/SECURITY_REVIEW_3_2.md`](docs/SECURITY_REVIEW_3_2.md), and [`docs/WINDOWS_UPGRADE_3_2.md`](docs/WINDOWS_UPGRADE_3_2.md). **Security review is scoped, not a complete Cloudflare audit or an enterprise security certification.** The AI practice grader is not validated for actual hiring.
