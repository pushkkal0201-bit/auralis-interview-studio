# Auralis 3.2 — Security and Evaluation Upgrade

- Corrects the first-900-characters grading flaw with multi-position, bounded chronological evidence excerpts.
- Adds optional first/latest score trajectories; rejects contradictory low scores and two known false electrical-engineering judgments rather than fabricating a revised grade.
- Replaces speculative question rationale with deterministic controller coverage state.
- Binds CodeProof source citations to owner-scoped, server-inspected evidence handles; discards unsigned client-provided source references.
- Adds common secret/token redaction and a 48-hour retention window for unclaimed inspected source evidence.
- Adds local model-call budgets to limit runaway Groq/Hugging Face quota usage, including connection checks and Groq transcription.
- Supports labeled offline plan, question, role comparison, parallel retry question and provisional assessment/feedback fallbacks.
- Provides retry of failed report grading and failed retry feedback after the selected provider recovers.
- Prints a concise assessment by default, with a separate full-transcript print option and expandable replay.
- Shows session model, AI provider, fallback provenance and answer evidence links in the report.
- Maintains Python 3.11 / FastAPI / SQLite / GPT-OSS / Windows CMD compatibility.
- Adds the scoped source-based Cloudflare-informed security review and test notes in `docs/`.
- **Not a fully certified security audit or validated hiring evaluation.** Browser and real cloud inference still require checks on the user's machine.
