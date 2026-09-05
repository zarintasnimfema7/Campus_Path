# Phase 3 route and operations audit

## Route inventory

| Classification | Routes | Authorization/data behavior |
|---|---|---|
| Public | `GET /`, `/health`, `/database/health` | Deliberate health endpoints; database failures have generic responses, never connection details. |
| Public | `/docs`, `/redoc`, `/openapi.json` | FastAPI API documentation; no user data. |
| Private | `POST /cv/analyze`, `/jobs/analyze`, `/skill-gap/analyze`, `/planner/generate` | Clerk required. Analyze caller-supplied content; no persisted resource reads/writes or client user-ID authorization. |
| Private | `POST /evidence/verify-github` | Clerk required. Existing inline task mode does not access persisted tasks. Optional `task_id` resolves the actual task through its owning plan before verification. |
| Private | `POST /replan` | Clerk required. Stateless computation over caller-supplied models; no persisted plan mutation or plan lookup. |
| Private | `POST /data/users` | Upsert by verified Clerk ID, never by client email; contact email comes only from verified auth data when present. |
| Private | `POST /data/jobs`, `/data/profiles` | Write under Clerk ID; legacy body `user_id` cannot override it. |
| Private | `POST /data/skill-gaps`, `/data/plans` | Clerk ID plus owned `job_targets.id` checked and locked in the write transaction. |
| Private | `POST /data/evidence` | Lock owned task via `tasks.plan_id → plans.id → plans.user_id` before evidence insert/task update; update also scopes through the plan owner. |
| Private | `POST /workflow/start` | Clerk identity, durable rate admission, existing upload/job/publish contract. |
| Private | `GET /workflow/{job_id}` | Existing UUID + Clerk user lookup, generic 404 for missing/wrong owner. No audit event per poll. |
| Internal | `POST /internal/workflow-jobs/process` | No Clerk dependency; service-to-service only. See deployment prerequisite below. |

All user-data routes were reviewed. There are no private list endpoints, direct
plan/task read routes, or evidence-ID update routes in the current API. Wrong-owner
and missing job/task lookups both return `404 Resource not found.` The actual Neon
column metadata was inspected read-only before adding ownership SQL.

The public persistence gap, unauthenticated standalone analyzers, email-based user
upsert, unscoped evidence update, raw authentication error print, and detailed
database/AI exception responses were corrected. Duplicate jobs-router registration
was removed. Inline AI computation does not prove submitted evidence is authentic;
it does not authorize access to another user's persisted resources.

## Worker deployment prerequisite (manual, later phase)

The internal worker route is deliberately unchanged and has no end-user Clerk
authentication. It must not be internet-accessible without service authentication.
The current FastAPI app mounts both user and internal routes: before deployment,
isolate the worker behind a service with Cloud Run IAM/invoker restrictions and
authenticated Pub/Sub delivery. Do not assume IAM protects one path of a publicly
invokable service. No GCP IAM configuration or deployment was performed here.

## Workflow start admission

`WORKFLOW_START_RATE_LIMIT=5` and `WORKFLOW_START_RATE_WINDOW_SECONDS=600` implement
a sliding window per verified Clerk user, shared by every instance through Neon.
Only positive integer configuration is accepted; configuration/database failures
fail closed with HTTP 503.

Within one READ COMMITTED transaction, obtain a namespaced SHA-256-derived
`pg_advisory_xact_lock`, count recent `workflow_start_reserved` events, then insert
either a reservation or rate-limit denial and commit. Counting and reserving never
release the transaction between them. The timestamp is taken after lock acquisition.
Hash collisions only serialize unrelated callers; counts remain user-scoped.
[PostgreSQL transaction advisory locks](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS)
release when the transaction ends.

GCS, workflow creation and Pub/Sub execute only after admission commits. A rejected
request returns 429 with generic retry-later wording. Attempts admitted before a
bad CV or downstream failure still consume a slot until the window expires; this
prevents repeated failing expensive operations from bypassing the limit. There is
no Redis, instance-local limiter, worker tuning, or external call under the lock.

## Audit storage and privacy

Migration `a3c720240001_create_access_logs.py` follows `55e064ea8ca4`. It adds only
`access_logs`: UUID id, nullable text user_id/resource_type/resource_id, required
text action/outcome, nullable JSONB metadata, and timestamptz created_at. An index
on `(user_id, action, created_at)` supports admission queries.

Events: workflow reservation/acceptance/rate limit, profile update, job save,
skill-gap save, plan save/replan, evidence submission/verification. Events describe
actual operations, not every request. Metadata permits only integer `http_status`;
actions/types/outcomes are allowlisted, resource IDs are UUIDs. Never pass content,
paths, URLs, email addresses, JWTs, credentials, exception text, or request bodies.
SQL values are parameterized. Best-effort business audit writes report only a
generic server log on failure; the rate-limit reservation is mandatory and fails
closed. Existing business `agent_runs`/`activity_logs` storage is not repurposed.

Apply the migration to the confirmed development Neon database with
`alembic upgrade head`, then `alembic current`, from backend using its virtualenv.
Do not run against an unconfirmed or production target. No fake audit rows are
needed for verification. Production migration application and access/retention
policy remain operational tasks; do not purge active reservations inside the
configured rate window. No retention scheduler is added in this phase.

Tests run without Neon writes: ownership queries, HTTP authorization, admission
transaction ordering/concurrent contenders using a lock simulation, audit privacy,
and all original async-workflow tests. This is not a live distributed load test.
