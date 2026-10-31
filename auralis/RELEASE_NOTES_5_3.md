# Auralis 5.3 · Practical Technical Interview Lab

Builds directly on the complete 5.2 application. **All previous features remain.**

## Features

- **Practical lab:** a new seventh navigation destination with editorial two-column workspace, Python and engineering tabs.
- **Five Python challenges:** sum_numbers, reverse_text, palindrome, range_span, clamp. Each has two public examples and three withheld edge cases.
- **Restricted AST expression interpreter:** exactly one `def solve(...)` with a single `return` expression, selected pure operators and built-ins. No `eval`, `exec`, AST compilation, Python subprocesses, imports, attributes, loops, recursion, file or network execution. This is intentionally **not full Python**.
- **Three engineering cases:** static load per support, 90° sheet-metal bend allowance, ideal beam deflection. Selected reference values are calculated by deterministic formulas using clearly stated assumptions. The 1% difference threshold checks arithmetic only, not engineering tolerances or safety.
- **Practice attempt tracking:** SQLite stores owner-scoped challenge ID, timestamp and pass count; *not* submitted code, free-text reasoning, or input values. Attempts capped at 200 per browser owner (latest 100 accessible), removed by Privacy > Delete all, subject to the existing retention policy. Existing interview tables are unchanged.
- **Separate practice history:** practice test scores do not inflate rubric-based Skill DNA interview scores.
- **No cloud key required** for either practical tab.

## Verification

- Python automated regression tests, old + new: 117 passed in the release environment.
- JS syntax checked with Node; live FastAPI health checked at 5.3.0; endpoint tests use TestClient.
- Controlled browser fixture using inline real HTML/CSS/JS and simulated APIs checked at 1440, 1024, 768, 390 and 360 px with no overflow or JavaScript errors. This is *not* end-to-end browser-to-localhost validation (hosted Chromium blocked navigation).
- Live Groq, microphone, and actual Windows installation still require user-device verification.

## Boundaries

This is a guided technical-practice environment. The Python subset is purposefully narrow, and passing selected tests cannot prove algorithmic correctness in general. Formula results do not validate an engineering design or replace qualified review.
