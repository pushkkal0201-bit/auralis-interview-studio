# Auralis 3.2 — Reliability, Evaluation & Regression Notes

## Motivating regression

The 45-page 3.1 electrical-engineering practice report said the candidate performed unrealistic current calculations, even though the replay included the correct illustrative three-phase estimates for 5 MW at 0.9 PF: approximately 7,730 A at 415 V and 292 A at 11 kV. It also graded only the first 900 characters of lengthy answers and failed to reflect later corrected power-factor formulas. The previous X-Ray rationale incorrectly described a previously assessed competency as unassessed.

## New evaluation path

- Full answer text remains in SQLite and in session replay.
- For long answers, select a bounded representative sample from the beginning, numerically detailed middle paragraphs and conclusion, in original order. All answer turns remain present; excerpting is explicitly disclosed.
- The model is instructed to provide first and latest scores on multi-answer competencies; a blanket 0/4 with an unsupported improvement trajectory fails validation. It is retried, then provisionally unscored if still invalid.
- Add two narrowly scoped deterministic checks (three-phase 5 MW load-current assertions and correctly restated P/Q/S power-triangle formulas). On direct contradiction, **withhold the grade**; the application does not invent a replacement grade.
- Score evidence in summary cards is bounded to short excerpts; full testimony appears under an expandable replay section. Use the concise print action for short reports.
- X-Ray coverage context comes from the controller's actual counts, not from an unverified model claim of prior coverage.
- Show the AI provider and session model in the report and preserve provenance for offline fallback.

## Fallback matrix

| Action | If cloud model is unavailable | What is *not* claimed |
|---|---|---|
| Build interview plan | Labeled, job-derived three-competency rubric; no remote model used | Personalized AI analysis |
| Generate interview question | Controller-selected, labeled local rubric question | Adaptive model generation |
| Grade final answers | Save all answers, return provisional report without numerical scores | Demonstrated competence |
| Retry graded report | Retry model when quota/connectivity returns | That a rejected report was valid |
| Parallel retry question | Local criterion-based retry task | A fresh AI problem |
| Grade retry answer | Save answer; show provisional feedback and allow retry | Validated improvement |
| Compare two roles | Return labeled local job-derived plan outlines | Live AI ranking |
| Transcribe speech | Browser recognition (with browser-vendor consent) or typed input | Offline transcription |
| GitHub unavailable | User can upload a source ZIP | That uploaded code was executed |

## Remaining evaluation limitations

This is an interview practice assistant, not a validated hiring tool. The scorer still depends on LLM reasoning for nuanced domain judgments. Bounded evidence sampling can omit content; broad, domain-specific factual verification and fairness testing remain future work. Offline sources never silently masquerade as live AI. No real Groq/Hugging Face requests were made for this release.

## Regression tests

`tests/test_assessment_integrity_v32.py` covers late calculations, all chronological answers, the false protection-current criticism, the false blanket 0/4 power-factor criticism, source citation spoofing, local free-tier call caps, deterministic X-Ray context, plan fallback, comparison fallback, retry feedback fallback and stored-answer continuity. The existing 3.1 coverage / scoring / privacy tests continue to run.
