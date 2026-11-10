# Voice mode

Real interviews are spoken. Voice mode makes the candidate explain out loud, which is the skill most people never practise.

## Candidate → you (speech input)

The candidate speaks through their agent's dictation feature:
- **Claude Code**: run `/voice`, then **hold Space** to talk and release to send (`/voice tap` for tap-to-start). It needs a Claude.ai login and a local microphone; it doesn't work over SSH or in cloud sessions.
- **Other agents**: their built-in dictation if available, otherwise the OS dictation feature (macOS: press the Dictation shortcut; Windows: `Win + H`).

At the start, tell them how to turn it on, in one line. Transcripts are messy. Interpret them generously, and never penalise transcription errors. Do penalise genuinely unclear explanations.

Code is still typed, or written in a file. Nobody dictates code.

## You → candidate (speech output)

Speak the interviewer's lines aloud with the OS's built-in text-to-speech, while also printing them:

| OS | Command |
|---|---|
| macOS | `say -r 185 "<text>"` |
| Linux | `spd-say "<text>"` or `espeak "<text>"` (if installed) |
| Windows (PowerShell) | `Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("<text>")` |

Check once that the command exists (`command -v say`). If none is available, stay text-only and say so.

Rules for spoken lines:
- **Speak only short interviewer turns**: the problem statement (in natural sentences, no symbols), questions, hints and acknowledgements. Never speak code, tables or scorecards.
- Keep each spoken line under about 40 words. Escape quotes properly in the shell command.
- Write numbers and symbols as words ("n up to ten to the fifth", not "n ≤ 10^5").

## Scoring in voice mode

Communication gets extra weight (25% instead of 20%; take the 5% from Speed). In the debrief, add:
- **Clarity**: could a listener follow the approach without seeing code?
- **Filler and rambling**: long, circular explanations.
- **Structure**: did they signpost ("First I'll…, then…")?
