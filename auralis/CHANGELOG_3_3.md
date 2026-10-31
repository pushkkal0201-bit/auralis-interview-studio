# Auralis 3.3 — Evaluation, Provenance and Export Reliability

Release scope: report problems discovered during the synthetic mechanical engineering interview in Auralis 3.2. **Not an independently validated hiring or engineering certification system.**

## Improvements

1. **Separate print modes.** Compact assessment omits the full transcript; full replay prints the transcript and always-visible Interview X-Ray explanations. Full answers now have safe Markdown-like rendering (`**bold**`, headings and lists) with `textContent`/text nodes, not HTML injection. Revised print CSS permits pagination within long answers, avoiding large empty areas and 46-page output for ordinary interviews. Standalone browser QA fixture: four-page compact and eleven-page full report for twelve long synthetic answers. Actual page counts depend on user content, printer and browser.
2. **Claim provenance.** New "fictional or synthetic test data" checkbox, recorded per session. All reports identify candidate history as either synthetic or self-reported/unverified. Report text normalizes selected unjustified claims of "verified professional experience" and "real-world project example"; it does not prove actual employment or execution.
3. **Next-score evidence.** Model schema optionally accepts `next_score_gap`, requested by the prompt for every score below 4. Reports display this next-rubric-step rationale or explicitly indicate when the model failed to supply one. No made-up achievements or practice verification is inferred.
4. **Question source and failure categories.** Question X-Ray records source (live/demo/local), generation attempts, repeated-question rejections and deliberate competency revisits. Local fallback events store safe error categories and counts, never provider exception bodies or tokens. Transient provider errors (including timeouts) receive one short bounded retry; rate limits and authorization failures do not.
5. **Reduced repetition.** Same-competency question selection checks normalized wording and topic-word overlap, including both near-identical mechanical-engineering and GD&T questions from the reviewed interview. Re-assessment after full skill coverage is explicitly labeled as a revisit; genuinely new scenarios may still revisit the same competency.
6. **Regression checks.** Added synthetic engineering tests for question duplication, provider failure classification, synthetic provenance, score-gap honesty, old-session compatibility, source tracking and print-mode structure. The existing 62 tests remain passing.

## Constraints and caveats

- Live GPT-OSS inference is **not** validated in this packaging environment. Run the interview plan, answer generation and scoring with your own key on Windows.
- The fallback taxonomy distinguishes transport, authentication, quota and invalid-question conditions without recording raw sensitive provider errors. This is not full observability or automated remediation.
- Topic-word overlap is a heuristic. It can reject a legitimately similar question, or miss a semantic paraphrase in another language; model retry then local rubric fallback stays clearly labeled.
- HTML print behavior depends on the browser, font availability and user-selected PDF settings. Print QA is a synthetic Chromium rendering test, not a guarantee of an exact page count.
- Scores are language-model practice judgments based on bounded evidence excerpts, not independently verified practical ability; a full replay remains available for manual review.
- Local storage is still not encrypted and should remain localhost only. Stop the old and new servers before copying `.data`.
- Groq/Hugging Face keys and private SQLite state are **not included** in this ZIP.
