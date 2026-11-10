# Coding interview rubric

Score each dimension 0–10. Anchor to these descriptions. When torn, pick the lower score and say why.

## Problem Solving
- **9–10**: Found the optimal approach independently, explained why it works, handled the follow-up variant.
- **7–8**: Reached optimal with at most a rung-1 nudge, or started sub-optimal and improved it themselves.
- **5–6**: Needed a rung-2 hint, or settled for a correct but sub-optimal approach.
- **3–4**: Needed rung 3 or 4, or reached an approach only after counterexamples.
- **0–2**: No working approach.

## Code Quality
- **9–10**: Clean, idiomatic, well named, no dead code, sensible helpers.
- **7–8**: Readable, minor naming or structure issues.
- **5–6**: Works but messy: magic numbers, deep nesting, copy-paste.
- **0–4**: Hard to follow, or mostly incomplete.

## Correctness & Testing
Score from the executed run in SKILL.md §5 (edge cases, random differential testing, max-size input), not from reading the code.
- **9–10**: Passed all cases including edge cases on the first run; dry-ran unprompted.
- **7–8**: Passed after fixing a bug they found themselves.
- **5–6**: Needed failing inputs shown to them to find bugs; edge cases missed.
- **0–4**: Fails core cases.

## Communication
- **9–10**: Asked the key clarifying questions, thought aloud throughout, explained trade-offs.
- **7–8**: Mostly clear; missed one important clarification or went quiet for a stretch.
- **5–6**: Needed prompting to explain; jumped to code.
- **0–4**: Little explanation; the interviewer could not follow.

## Complexity Analysis
- **9–10**: Correct time and space complexity, stated unprompted, with justification.
- **7–8**: Correct when asked.
- **5–6**: Partially correct (e.g. right time, wrong space).
- **0–4**: Incorrect or unable.

## Speed
Against a 45-minute round for one medium problem:
- **9–10**: Optimal working code in ≤ 25 min.
- **7–8**: ≤ 35 min.
- **5–6**: ≤ 45 min.
- **0–4**: Over time or unfinished.
Scale proportionally for other durations and difficulties.

## Overall and verdict

Overall = weighted mean, rounded: Problem Solving 30%, Correctness & Testing 20%, Communication 20%, Code Quality 10%, Complexity 10%, Speed 10%.

| Overall | Verdict |
|---|---|
| 9–10 | Strong Hire |
| 7.5–8.9 | Hire |
| 6.5–7.4 | Lean Hire |
| 5–6.4 | Lean No Hire |
| 3–4.9 | No Hire |
| 0–2.9 | Strong No Hire |

**Hard caps:** a rung-4 hint caps the verdict at Lean No Hire. Code that fails core cases at the end caps it at No Hire.
