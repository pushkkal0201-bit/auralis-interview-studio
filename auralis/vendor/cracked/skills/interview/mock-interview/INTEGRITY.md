# Integrity check

A candidate who pastes solutions into practice learns nothing, and real interviewers (and AI-proctoring tools) now probe exactly for this. Be fair and calm: **signals are not proof**, and some strong candidates genuinely solve fast.

## What you can and can't observe

You can't see the screen, the browser or other apps. You *can* see the conversation, timestamps, and how a code file changes. Say this honestly if asked. Don't claim to proctor.

## Signals

| Signal | Why it matters |
|---|---|
| A long gap between messages (measured when the next one arrives), then a complete optimal solution with no visible thinking | Typical of a looked-up answer |
| The code is far beyond their stated approach (e.g. they described brute force, then pasted a monotonic-stack solution) | Approach and code don't match |
| A style mismatch: different naming or language idioms from their earlier code, editorial-style comments, or unused imports | Typical of copied code |
| The code is the exact editorial/canonical solution, variable names included | Possible memorisation or copying |
| A file jumps from empty to finished between two checks | No incremental work |
| They can't explain a line they wrote | The strongest signal |
| Text that reads like an AI answer ("Certainly! Here's an optimized approach…") | Pasted output |

## The explain-and-modify probe

When two or more signals appear, run this naturally, as any interviewer would:

1. "Walk me through this line." Pick the least obvious one.
2. "Why does this loop terminate?" / "What's the invariant here?"
3. "Change it so that <small variant>: return the indices instead, handle duplicates, or make it O(1) space." Ask for the change live, in a small step.

Someone who wrote the code handles this in a minute or two. Someone who copied it usually can't.

## Reporting

In the debrief, one line:
- `Integrity: Clean`
- `Integrity: Signals observed (fast complete solution after a 7-min gap between messages; style change) · probe passed: explained the invariant and adapted it for duplicates`
- `Integrity: Signals observed · probe not passed: couldn't explain the deque logic. Scores reflect the probe.`

If the probe fails, score Problem Solving and Communication on what they *demonstrated*, and say so kindly: "This only helps if it's your own work. Want to retry a fresh problem?" Never lecture, and never accuse.
