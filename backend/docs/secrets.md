# Secrets and production environment preparation

No secrets, cloud resources, service settings, or deployments were created.

## Future secret injection

Secret Manager secret version → environment variable → FastAPI/worker process.
Use Cloud Run's native secret environment mapping, pinned to reviewed versions;
grant its service identity access only to required secrets. Rotate versions through
the later deployment process. See Google's
[Cloud Run secret configuration](https://cloud.google.com/run/docs/configuring/services/secrets).

| Variable | Treatment |
|---|---|
| `DATABASE_URL` | Secret Manager; existing Neon/psycopg connection string. |
| `CLERK_SECRET_KEY` | Secret Manager for API authentication; never browser-visible. |
| `GEMINI_API_KEY` | Secret Manager for existing Gemini/ADK configuration. |
| `GITHUB_TOKEN` | Secret Manager; existing optional GitHub API credential. |
| `APP_ENV`, `FRONTEND_URL`, `CLERK_AUTHORIZED_PARTIES` | Regular environment configuration; exact production HTTPS origins. |
| `GOOGLE_CLOUD_PROJECT`, `GCS_BUCKET_NAME`, `PUBSUB_TOPIC_ID` | Regular configuration of existing resources. |
| `GOOGLE_GENAI_USE_VERTEXAI` | Existing provider-selection configuration; not a secret. |
| `WORKFLOW_MAX_RETRIES` | Existing retry policy; unchanged. |
| `WORKFLOW_START_RATE_LIMIT`, `WORKFLOW_START_RATE_WINDOW_SECONDS` | Regular config; defaults 5 and 600. |

Use Application Default Credentials locally and attached service identity later;
do not package service-account JSON. No new credential mechanism is needed.
Worker/API variables should be supplied only where used. Alembic currently reads
the local `backend/.env` database target; do not check it in or bake it into artifacts.
Choose the future migration execution environment separately during deployment.

## Frontend / Vercel (manual, later)

`NEXT_PUBLIC_API_URL` is intentionally public. Clerk's
`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is also intentionally public and identifies the
matching instance. `CLERK_SECRET_KEY`, if needed by Next's server-side Clerk
middleware, must remain a server-only Vercel variable. Never prefix database,
Gemini, GitHub, or Clerk secret keys with `NEXT_PUBLIC_`. Public route/redirect
settings are configuration, not credentials. Use separate preview/production
values; no Vercel settings were changed.

## Repository audit

Tracked-file scans used `git grep -l` plus filename checks without printing values.
No matching tracked Clerk/Gemini/GitHub/private-key/database credentials were
found outside test fixtures. Local backend/frontend `.env` files are untracked and
ignored. `.env.example` remains tracked with empty secret placeholders. Common
private-key and service-account filenames are ignored too. Pattern scanning is a
targeted check, not proof that every possible secret format is absent.

Never include secret values, raw environment files, CV text, or JWTs in bug reports,
audit records, tool output, or application logs. Keep development files local and
configure production values through the respective managed environment controls.
