# Upgrade from Auralis 3.2 to Auralis 3.3 (Windows CMD)

1. In your old Auralis 3.2 server window, press **Ctrl+C**. This matters because SQLite may still be writing to `.data/auralis.sqlite3` and its WAL sidecars.
2. Extract `Auralis_3_3_Evaluation_And_Export_Fixes.zip` into `D:\Auralis_3_3_Evaluation_And_Export_Fixes`. The application directory should be `D:\Auralis_3_3_Evaluation_And_Export_Fixes\auralis`.
3. Open a **new Command Prompt** and type the following commands **one line at a time**, without copying `D:\...>` prompt characters:

```bat
cd /d "D:\Auralis_3_3_Evaluation_And_Export_Fixes\auralis"
copy "D:\Auralis_3_2_Security_And_Evaluation_Upgrade\auralis\.env" ".env"
xcopy "D:\Auralis_3_2_Security_And_Evaluation_Upgrade\auralis\.data" ".data\" /E /I /H /Y
setup.bat
start.bat
```

Only use the `copy` command if the previous `.env` file exists. Keep `.env` secret; never send it to ChatGPT or GitHub. If your old `.data` directory doesn't exist, skip `xcopy`: Auralis creates fresh local data automatically.

4. Open the **exact localhost URL** printed by the launcher; normally `http://127.0.0.1:8000` but it may select another port.
5. In a second CMD window, check `curl http://127.0.0.1:8000/api/health` if the displayed port is 8000. Look for `"version":"3.3.0"`. This only verifies backend readiness, **not** that a real Groq inference succeeded.
6. Under Interview setup, tick **fictional or synthetic test data** for mock CVs, select your provider, and build a new plan. Submit an intentionally incorrect answer, then a corrected one; assess the final Skill DNA. Check both print buttons and provider fallback log.

## Migration and privacy

- The new release reads old 3.2 session snapshots and reports. Existing reports will not gain AI-generated `next_score_gap` rationales retroactively; the UI explicitly says when that explanation was not recorded. **Newly generated reports** use the 3.3 schema.
- Preserve the prior 3.2 folder as a backup until you confirm old history appears in 3.3.
- Do not copy the `.venv` directory across releases. `setup.bat` creates a new environment.
- Do not paste Python / CMD prompts into commands. Stop both servers before transferring SQLite data.
- Local-first application is not hardened for public Internet hosting.
