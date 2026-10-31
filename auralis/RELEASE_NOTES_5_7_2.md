# Auralis 5.7.2 — Security hardening

Source for this security-focused update: the user-provided Auralis 5.7.1 ZIP.
Method: focused trust-boundary source review informed by Cloudflare's
`security-audit-skill` (https://github.com/cloudflare/security-audit-skill).
This is not an endorsement or audit certificate from Cloudflare.

## Changed
- Hosted HTTPS origin and Fetch Metadata checks.
- Hosted hostnames: invalid, wildcard or pathful public URL rejected.
- Hosted account endpoint usage throttling shared in PostgreSQL and not storing
  plaintext emails or authentication tokens.
- Invalid provider checks rejected before AI usage budget is decremented.
- `X-Frame-Options`, HTTPS HSTS and browser `Permissions-Policy` headers.
- Full account-record erasure also clears the owner's AI quota event rows.
- New standalone retention job for managed daily scheduling.
- Updated Windows launcher release label and deployment instructions.
- Added dedicated security regressions and a scoped review report.

## Tested
Sandboxed local tests: 171 passed, 1 optional real PostgreSQL test skipped.
No production credentials, live Supabase SMTP, managed PostgreSQL, provider
inference, external WAF or deployed infrastructure were used.

## Read first
`SECURITY_REVIEW_5_7_2.md` and `DEPLOY_5_7_2.md`
