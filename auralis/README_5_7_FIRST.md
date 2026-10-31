# Auralis 5.7 | Production Foundation

- Offline Windows/local development: `setup.bat` then `start.bat` (SQLite, localhost, existing historical behavior).
- Hosted production: read `DEPLOY_5_7.md` **before setting any environment variables**.
- Cloud mode demands a PostgreSQL database, verified Supabase login and a real Groq key at startup; no silent live-question fallback.
- GitHub repository **must not include `.env`, `.data`, `.venv` or SQLite files**.
- Do not confuse completed local tests with a completed real-cloud security review or a production launch.
