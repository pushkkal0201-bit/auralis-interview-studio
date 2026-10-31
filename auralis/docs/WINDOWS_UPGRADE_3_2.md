# Auralis 3.2 — Windows CMD upgrade

1. **Close all Auralis 3.1 server CMD windows** with Ctrl+C. In particular, stop the instance serving port 8002.
2. Extract `Auralis_3_2_Security_And_Evaluation_Upgrade.zip` to `D:\Auralis_3_2_Security_And_Evaluation_Upgrade` (or another location); enter its inner `auralis` folder.
3. Optionally copy the private `.env` and `.data` directory **after the old server is stopped**. Existing session data and keys are not bundled in the new ZIP.
4. Run `setup.bat`, then `start.bat`. The launcher selects the next free localhost port.
5. Open the exact URL printed by CMD; do not assume port 8000. Check `/api/health` for version `3.2.0`.
6. Choose Live GPT-OSS / Groq and your model, consent, and test a sample interview. If the provider is down, check the visible **LOCAL RUBRIC FALLBACK** label. Never treat local questions or provisional feedback as scored AI evaluation.
7. At the end, choose **Print concise assessment**. Use **Print full replay** only if you want the complete interview transcript.

### Example CMD commands

```
cd /d "D:\Auralis_3_2_Security_And_Evaluation_Upgrade\auralis"
copy "D:\Auralis_3_1_Industry_Hardening_Fallbacks\auralis\.env" ".env"
xcopy "D:\Auralis_3_1_Industry_Hardening_Fallbacks\auralis\.data" ".data\" /E /I /H
setup.bat
start.bat
```

Use the actual extraction paths if different. Never share `.env`, `.data`, or `backups` publicly. To keep older local sessions set `AURALIS_RETENTION_DAYS=0` in `.env` **before** first startup. Existing sessions remain readable; CodeProof uploads should be re-inspected to obtain a server-verified evidence handle.

### Optional local provider budget

In `.env`:

```
AURALIS_MAX_CALLS_PER_MINUTE=15
AURALIS_MAX_CALLS_PER_HOUR=90
```

These are per running process, not a billing guarantee. Groq/Hugging Face provider rate limits still apply.
