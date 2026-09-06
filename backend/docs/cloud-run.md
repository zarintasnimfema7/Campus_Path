# Shared backend container preparation — Phase 4

Repository preparation only. Docker/WSL are not installed on the current Windows
machine. Local image build and runtime verification are **PENDING**. The image will
later be built in Google Cloud or CI; that infrastructure is outside this phase.
No installation, Docker build/run, deployment, or remote settings changes occurred.

## Image and startup

Use `backend` as the build context with `backend/Dockerfile`. One image serves both
`campuspath-api` and `campuspath-worker`; no source duplication is needed.
The base is `python:3.12-slim`, with `/app` as the working directory. Requirements
are copied before source for layer caching and installed with
`pip install --no-cache-dir -r requirements.txt`, followed by `pip check`.
Missing direct runtime dependencies were added with pins from the existing Python
3.12 environment; requirements encoding was normalized from UTF-16 to UTF-8.
Transitive dependency resolution and Linux wheel availability still need validation
in the later build. This is not a hash-locked environment; the base tag tracks
upstream patch updates.

Only `app/` and the entrypoint are copied after requirements. No compiler, process
manager, frontend, migrations, local virtualenv, or environment file is copied.
The application runs as UID/GID 10001 with a writable home. Source remains owned
by root and readable by the application user. No extra system packages are installed.

```sh
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}" --workers 1
```

There is no reload mode or startup migration. `exec` makes Uvicorn PID 1 so SIGTERM
reaches it directly. `.gitattributes` enforces LF for the shell script on Windows.
Default port is 8080, overridden by Cloud Run's `PORT`. `EXPOSE` documents the default;
it does not bind a host port. See the
[Cloud Run container contract](https://cloud.google.com/run/docs/container-contract).

## Runtime configuration and ADC

Supply configuration externally following `.env.example` and [secrets.md](secrets.md).
Keep `DATABASE_URL`, `CLERK_SECRET_KEY`, `GEMINI_API_KEY`, and optional `GITHUB_TOKEN`
out of build arguments/image layers. Regular runtime variables include `APP_ENV`,
`FRONTEND_URL`, `CLERK_AUTHORIZED_PARTIES`, `GOOGLE_GENAI_USE_VERTEXAI`,
`GOOGLE_CLOUD_PROJECT`, `GCS_BUCKET_NAME`, `PUBSUB_TOPIC_ID`, `WORKFLOW_MAX_RETRIES`,
`WORKFLOW_START_RATE_LIMIT`, and `WORKFLOW_START_RATE_WINDOW_SECONDS`.

`SERVICE_ROLE` selects routes at startup: `api` (default) or `worker`. Any other
value fails with a clear configuration error. Both roles retain database startup
configuration; only the API router imports require Clerk configuration. `/health`
itself is lightweight, but startup retains
the existing database pool initialization. Neon schema/pooling are unchanged.
Apply migrations separately before using dependent endpoints; startup never runs
Alembic. This image does not package a migration runner.

GCS/Pub/Sub continue using ADC; Cloud Run will use its attached service identity.
Do not copy service-account JSON or point `GOOGLE_APPLICATION_CREDENTIALS` at a
committed file. If local Docker is used later, a developer may read-only mount their
external ADC file and configure its mounted path at runtime, ensuring UID 10001
can read it. Never place credentials in the build context. No credentials were created.

`.dockerignore` excludes environments, caches, Git/IDE files, tests/coverage, logs,
temporary files, ADK state, credential JSON patterns and private keys. Explicit
COPY statements further limit contents. This is a static context review; no image
has been built or inspected.

## Planned services — manual configuration later

| Setting | campuspath-api | campuspath-worker |
|---|---|---|
| Image | Shared backend image | Same image |
| SERVICE_ROLE | api (default) | worker |
| Port | 8080 | 8080 |
| Starting concurrency | 8 | 1 |
| Minimum instances | 0 | 0 |
| Initial maximum instances | 5 | 3 initially; consider 5 after measurement |
| Initial request timeout | 60 seconds for enqueue/status traffic | 600 seconds, subject to validation below |
| Intended traffic | User routes authenticated with Clerk | Authenticated Pub/Sub push only |

These are initial tuning recommendations, not permanent limits or remotely applied
settings. Later load testing must consider Gemini quotas, Neon connections, cost,
cold starts and latency. The unchanged pool allows up to 10 connections per process;
budget connections across both services. No pool/concurrency tuning is performed.
The primary API flow enqueues work; the worker executes the long AI workflow.

The app factory registers routes for the selected role only. `campuspath-api` may
be a public Cloud Run service later: Clerk protects private application routes,
and `/internal/workflow-jobs/process` is absent (404). API health, root, database
health and local API documentation remain available. Review legacy standalone AI
routes before applying the API's short timeout.

`campuspath-worker` exposes only `/health` and the internal push route. Normal
user routes, root, database health, and documentation endpoints are absent (404).
Both roles use the same image and `app.main:app` entrypoint; no business logic is
duplicated. Cloud Run IAM remains required during deployment even with route
isolation; role selection is not service-to-service authentication.

The worker receives `POST /internal/workflow-jobs/process`, to be protected later
with Cloud Run IAM and an authorized Pub/Sub push identity. Do not add Clerk to
that route or allow normal users to invoke it.

## Worker timeout boundary

The workflow downloads/extracts the CV, runs sequential combined job/CV and planner
AI stages, then persists results. There is no measured worst-case duration or
end-to-end deadline in the repository. No live AI call was made to estimate one.

Retain the existing 600-second Pub/Sub assumption and initially plan a 600-second
worker request timeout. This works only when the whole request, including transport
and cold-start overhead, finishes comfortably inside that window. Pub/Sub uses its
ack deadline as the push request timeout, capped at 600 seconds. Increasing Cloud
Run's timeout cannot extend Pub/Sub's waiting period. See the
[subscription contract](https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.subscriptions).

Duration compatibility is **unverified**, not guaranteed. Validate with headroom
later. Timeouts/disconnects do not guarantee ongoing Python/AI work stops. Preserve
atomic claims and [existing retry/DLQ behavior](pubsub.md); nothing changes those
semantics here. Cloud Run's short SIGTERM shutdown window also cannot guarantee
completion of long jobs; the documented stale-claim limitation remains.

## Verification without Docker

Run `python -m compileall app` and `python -m unittest discover -s tests -q` from
backend using its virtualenv, plus `git diff --check` from the repository.
Container preparation tests check the entrypoint and exercise `/health`, `/docs`,
and malformed worker input with FastAPI's test client without AI or database work.

Later validate Linux dependency installation/imports, non-root startup, default and
custom `PORT`, `/health`, `/docs`, malformed worker response, SIGTERM behavior and
image contents using Docker or a cloud builder. Use `/health`, not `/database/health`,
for a lightweight probe. Do not send real jobs just to verify route availability.
No new health endpoint or expensive Docker health command is introduced.
