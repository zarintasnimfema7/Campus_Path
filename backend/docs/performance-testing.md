# Reliability and performance validation — Phase 6

## What repository tests establish

| Behavior | Evidence |
|---|---|
| Same-user starts | Three concurrent starts publish distinct jobs using the same verified user's ordering key. |
| Multiple users | Concurrent A/B/C starts retain separate ordering keys; no global ordering key. |
| Atomic claim | Existing SQL tests require one conditional `UPDATE ... WHERE status = 'queued' RETURNING ...`; no read-then-write claim. |
| Duplicate delivery | Sequential and overlapping deliveries run AI/finalization once under simulated claim ownership. Completed redelivery is acknowledged without work. |
| Failure handling | Download/AI failure, completion-update failure and retry-update failure remain covered by existing tests. |
| Retry cap | Processing failures 1–4 increment retry_count and requeue; failure 5 becomes failed. Success does not increment. Non-2xx responses request redelivery; no manual republish. |
| Authorization | Existing workflow owner-scoped read, job/plan/task ownership, foreign-task evidence rejection and trusted Clerk-ID tests run in full CI. No private list endpoint currently exists. |
| Operations | Rate admission concurrency/configuration, sanitized audit fields, no per-poll auditing and API/worker role isolation remain covered. |

These tests use mocked services and lock/state simulations. They verify application
logic, SQL predicates and publisher metadata, **not actual database contention or
remote Pub/Sub ordering**. No new optional database integration suite was needed;
normal CI never uses a real Neon development or production URL.

Pub/Sub ordering still requires ordered subscription configuration and consistent
regional publishing. It orders published messages, not HTTP arrival or job creation
time. Duplicate delivery remains possible. Retry delays can block later same-user
messages; other keys remain independent. DLQ forwarding/attempt counts are best-effort.
See [existing Pub/Sub operations](pubsub.md).

## Stale processing is a known limitation

A worker disappearing after claim but before completion/failure persistence can
leave `status=processing`. Redelivery then receives no claim, returns non-2xx and
does not rerun AI. The disappearance test explicitly preserves that state; no test
pretends it self-recovers. Completion-write failures may have the same operational
symptom, and detailed persistence can be partial before a retry.

Future recovery should use measured durations plus a lease/heartbeat or carefully
reviewed stale-job procedure. Any recovery design must reject late finalization
from old owners and account for side effects already committed. No automatic reset,
lease system or manual republish mechanism was added here. Investigate ambiguous
jobs before any operator intervention.

## Safe load-test tool

`scripts/load_test.py` uses existing httpx and only sends **GET /health**. It does
not support workflow submission, CV upload, AI execution or automatic retries.
Supply `BASE_URL` explicitly; no environment/production default exists.

```sh
python scripts/load_test.py --base-url http://127.0.0.1:8000 --concurrency 4 --request-count 20
# Only for an explicitly approved staging host:
python scripts/load_test.py --base-url https://your-approved-staging.example --allow-remote --concurrency 4 --request-count 20
```

Environment equivalents: `BASE_URL`, `CONCURRENCY`, `REQUEST_COUNT`. An optional
`AUTH_TOKEN` environment variable sets a bearer header; avoid tokens on the command
line. Every non-loopback hostname, including obvious production URLs, requires the
explicit `--allow-remote` flag. Remote HTTP, embedded credentials, paths, query
strings and fragments are rejected. Confirm the target is approved staging; the
flag is not authorization to test production. Redirects and environment proxies
are disabled, TLS verification remains enabled, and each request has a ten-second
timeout. Defaults are four workers and twenty requests, bounded to 100 workers and
100,000 requests. Work is distributed among a fixed number of tasks rather than
creating one asyncio task per request.

Output includes total requests, successes, failures, requests/sec, average latency,
p50/p95/p99 milliseconds and status-code counts. Latency measures response headers
plus stream closing; bodies are not retained/downloaded. Percentiles use nearest
rank across all attempts, including errors. Redirects/non-2xx/network errors count
as failures, and failures produce a nonzero exit code. No token, body, target URL,
or raw network exception is printed. This is HTTP health latency, not job throughput.

Tool safety/concurrency/metrics are tested with httpx MockTransport. **No real load
test was run. Real load testing remains pending an approved staging deployment.**
Mock timing is not a production performance result.

## Database pool budget

`app/database/neon.py` currently has `min_size=1`, `max_size=10`. The shared image
runs one Uvicorn process. Starting service limits in [cloud-run.md](cloud-run.md):

`5 API instances × 10 + 3 worker instances × 10 = 80 theoretical connections`.

With five worker instances, that becomes 100. Eight warmed instances initially
hold at least eight pool connections; min service instances remain zero. Deployment
overlap, administrative/migration connections and other applications add to these
figures. Confirm the Neon compute/connection budget before launch. Prefer Neon's
pooled `DATABASE_URL`; pooler client connections and underlying server connections
are different limits. No measured budget violation is known, so the pool is unchanged.
No PgBouncer or additional pool layer is introduced.

## Concurrency and Redis

Keep API starting concurrency 8 and worker concurrency **1**, with worker maximum
instances **3** initially. In staging, evaluate worker concurrency 1 → 2 → 4 only
after measuring job duration, CPU, memory, Gemini quota/rate errors, Neon connections
and application error rate. Stop/revert a step when results regress; do not raise
concurrency based on mocks or theoretical throughput.

Redis is **not justified yet**. Durable PostgreSQL admission and the current async
pipeline address present requirements. Add caching/coordination only if measurements
show a specific bottleneck and demonstrate a benefit.

## Phase 7 validation boundary

Prepared CI can validate Linux Docker installation/build, but that job has not yet
run on GitHub. Local tests do not establish actual Pub/Sub ordered delivery, DLQ
forwarding, Cloud Run autoscaling/concurrency, production Gemini quotas, or
end-to-end GCS/PubSub/worker latency. Those require separately authorized Phase 7
integration/staging checks. No cloud resources or production workloads were used.
