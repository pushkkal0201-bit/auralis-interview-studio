# Auralis 5.7 | Production Foundation

## Included

- Hosted mode must use actual Groq credentials, a real PostgreSQL DATABASE_URL, and Supabase Auth.
- Email/password registration and login via Supabase Auth; server-verified session ownership.
- HTTP-only refresh cookies, short-lived access tokens in browser memory, password recovery workflow.
- Old browser-generated owner tokens rejected in authenticated mode.
- Existing SQLite tables use a PostgreSQL database adapter when hosted, including upserts and schema-creation translations.
- Model-provider errors do not silently generate scripted interview questions in hosted mode.
- Answer text is saved before a paid follow-up question call; failed generation pauses the session and offers a resume action.
- Host validation remains explicit, cloud service refuses missing production mode.
- Localhost development works with the existing SQLite and offline practice behavior.

## Not yet independently verified

- Live managed PostgreSQL, real Supabase provider, real Groq key and email delivery all require user-owned credentials and deployment.
- Multi-instance concurrency, institutional roles, per-account rate limits, account deletion from Supabase,
  external security review and data-protection compliance require additional work before public commercialization.

## Changes from old local data

Cloud user IDs are verified Supabase identities. Old local browser token histories
cannot be assigned to an account automatically; this would be unsafe. Explicit migration
requires user consent and verified ownership.
