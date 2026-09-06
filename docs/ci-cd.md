# CI/CD and database operations — Phase 5

`.github/workflows/ci.yml` validates pull requests and pushes to `main`, `dev`,
`feature`, and `feature/**`. Those match the current main/dev/feature workflow;
PRs from any branch are also checked. Concurrency groups use the head repository
and branch, so an obsolete push/PR run for the same source branch can be cancelled.
All jobs must pass; lint/build errors are not ignored.

## Verification jobs

| Job | Checks |
|---|---|
| Backend | Python 3.12, pip cache keyed by requirements, install requirements, `pip check`, `compileall app`, complete `unittest discover -s tests -q`. |
| Frontend | Node 22, npm cache keyed by package-lock, `npm ci`, lint, Phase 2 code checks, production build. |
| Migrations | Python 3.12, `alembic heads`, revision import/AST checks, exactly one head, PostgreSQL offline SQL generation. |
| Docker | Linux `docker build -t campuspath-backend:ci ./backend`, including dependency installation and `pip check`; no image push. |

The frontend build uses a syntactically valid, nonfunctional `pk_test_` fixture for
`ci.clerk.invalid` and a loopback API URL. It has no secret Clerk key or usable
account. This tests compilation/prerendering, not sign-in. The fixture is not a
deployment configuration. Clerk validates publishable key syntax; actual runtime
authentication remains unchanged. Public vs secret configuration is described in
[Clerk's environment documentation](https://clerk.com/docs/guides/development/clerk-environment-variables).
The existing Next font build may require outbound access to Google Fonts.

The historical OTP lint error was fixed by reading session storage through React's
external-store hook with an empty server snapshot. Registration, OTP verification,
and Clerk session finalization were not replaced or bypassed.

Normal CI uses mocks for Neon, Clerk, GCS, Pub/Sub and Gemini and never applies
migrations or submits real jobs. The workflow has only `contents: read`, does not
persist checkout credentials, uses timeouts and cancellation, and does not request
deployment secrets, registry login, or OIDC permissions. It uses `pull_request`,
not privileged `pull_request_target`. See
[GitHub workflow permissions/concurrency](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).

Local Docker/WSL are unavailable: the Linux image job is prepared, not verified by
a local build. GitHub execution is still pending a push; no workflow was pushed or
manually dispatched by this task. Static validation is not evidence of a successful
GitHub-hosted run. The image remains shared between `SERVICE_ROLE=api` and `worker`.

## Alembic developer operations

From backend with its Python environment active:

```sh
alembic heads
python scripts/check_migrations.py
alembic current
alembic revision -m "describe the schema change"
# Review the generated migration before the following database mutation:
alembic upgrade head
```

`heads` and the checker need no database. Offline mode uses the PostgreSQL dialect
directly and never loads `.env`. `current` and online `upgrade` use an explicitly
supplied `DATABASE_URL` first, then local `backend/.env`; confirm the intended
database before using either. The checker imports every migration, requires one
head, and generates SQL without applying it. Normal CI contains neither credentials
nor an online migration command.

The revision history begins after existing core tables were created manually.
Generating valid SQL does **not** mean `upgrade head` can bootstrap an empty DB:
the first tracked migration references existing `users`. For a new production
database, first establish and review the prerequisite schema/baseline in a separate
database-operations step. Never blindly stamp an empty database or treat offline
validation as proof of schema compatibility.

## Future deployment sequence — not implemented

1. All CI checks pass on the reviewed commit.
2. Build the release image from that commit in the chosen cloud pipeline.
3. Apply reviewed Alembic migrations **once**, using a separately authorized,
   serialized migration step with confirmed target, backup/recovery plan and schema baseline.
4. Deploy the API with `SERVICE_ROLE=api`.
5. Deploy the worker with `SERVICE_ROLE=worker` and required IAM.
6. Run authorized smoke/integration checks.

Never run migrations at container startup or let API and worker race to migrate.
The runtime image omits migration source and never migrates on startup;
the migration step must use the reviewed repository revision and its dependencies.
Use backward-compatible migrations and review rollback compatibility separately.

Frontend deployment ownership remains Vercel Git integration; do not add a second
frontend deployment pipeline in GitHub Actions. Backend/worker deployment belongs
to a later Google Cloud Run pipeline. No deployment, registry push, infrastructure,
DNS, production Clerk, or Secret Manager configuration is part of this phase.
