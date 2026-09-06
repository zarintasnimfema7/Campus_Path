# Workflow retries and dead-letter deployment

Application setting `WORKFLOW_MAX_RETRIES=5` caps total processing attempts,
including the first attempt. Invalid/nonpositive values fall back to 5.
Failures 1–4 increment the database counter and return to queued, clearing
started_at/completed_at. Failure 5 increments to 5 and becomes failed with a
completion timestamp. Success does not increment the counter. Errors are generic.

The worker returns 500 after processing failures, including terminal failure.
After an unsuccessful atomic claim, a read-only lookup determines acknowledgment:
missing/completed return 204; queued/processing/failed return 500 without AI work.
The lookup does not acquire ownership. Optional deliveryAttempt is accepted and
ignored; only the atomic database counter controls application attempts.
No application retry loops or manual republishing are implemented.

## Planned resources

| Resource | Suggested name / setting |
| --- | --- |
| Main topic | campuspath-workflow-jobs |
| Source push subscription | campuspath-workflow-worker |
| Push endpoint | POST /internal/workflow-jobs/process |
| Dead-letter topic | campuspath-workflow-jobs-dlq |
| DLQ subscription | campuspath-workflow-jobs-dlq-sub |
| Maximum delivery attempts | 5 |
| Ack deadline | 600 seconds |
| Retry backoff | Minimum 10 seconds, maximum 60 seconds |

Actual resource names are supplied during deployment. The dead-letter policy
belongs to the **source subscription**, not its topic. Attach a subscription to
the DLQ topic so forwarded messages can be retained and inspected.

Pub/Sub owns redelivery on unsuccessful push responses. Dead-letter forwarding
and delivery-attempt counts are best-effort: forwarding can occur before or after
five deliveries. The database count records processing failures, not transport
deliveries, so five application attempts are a cap, not a guarantee. See
[dead-letter topics](https://docs.cloud.google.com/pubsub/docs/dead-letter-topics)
and [subscription retry policy](https://docs.cloud.google.com/pubsub/docs/subscription-retry-policy).

## Deployment examples — do not run as application startup code

These commands are documentation only; replace every angle-bracket placeholder.
Use an existing authenticated Cloud Run worker service. Configure its request
timeout consistently with the 600-second push deadline and expected work time.
Do not expose the internal route through an unauthenticated public service.

```sh
gcloud pubsub topics create <MAIN_TOPIC> --project=<PROJECT_ID>
gcloud pubsub topics create <DLQ_TOPIC> --project=<PROJECT_ID>
gcloud pubsub subscriptions create <DLQ_SUBSCRIPTION> --topic=<DLQ_TOPIC> --project=<PROJECT_ID>
gcloud pubsub subscriptions create <SOURCE_SUBSCRIPTION> --project=<PROJECT_ID> --topic=<MAIN_TOPIC> --push-endpoint=<WORKER_BASE_URL>/internal/workflow-jobs/process --push-auth-service-account=<PUSH_SERVICE_ACCOUNT_EMAIL> --push-auth-token-audience=<WORKER_BASE_URL> --dead-letter-topic=projects/<PROJECT_ID>/topics/<DLQ_TOPIC> --enable-message-ordering --max-delivery-attempts=5 --ack-deadline=600 --min-retry-delay=10s --max-retry-delay=60s
```

Required IAM must be configured separately. The Pub/Sub service agent needs
publisher on the DLQ topic and subscriber on the source subscription. The push
identity needs Cloud Run invoker. Provisioning operators need permission to act
as the push identity; ensure the service agent can mint its OIDC token.

```sh
gcloud pubsub topics add-iam-policy-binding <DLQ_TOPIC> --project=<PROJECT_ID> --member=serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-pubsub.iam.gserviceaccount.com --role=roles/pubsub.publisher
gcloud pubsub subscriptions add-iam-policy-binding <SOURCE_SUBSCRIPTION> --project=<PROJECT_ID> --member=serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-pubsub.iam.gserviceaccount.com --role=roles/pubsub.subscriber
gcloud run services add-iam-policy-binding <WORKER_SERVICE> --project=<PROJECT_ID> --region=<REGION> --member=serviceAccount:<PUSH_SERVICE_ACCOUNT_EMAIL> --role=roles/run.invoker
gcloud iam service-accounts add-iam-policy-binding <PUSH_SERVICE_ACCOUNT_EMAIL> --project=<PROJECT_ID> --member=serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-pubsub.iam.gserviceaccount.com --role=roles/iam.serviceAccountTokenCreator
```

See the [gcloud subscription reference](https://docs.cloud.google.com/sdk/gcloud/reference/pubsub/subscriptions/create).
No commands were executed and no resources or IAM bindings were created in Step 10.

## Operational limits

A crash or failed retry/completion write can leave a job processing. Subsequent
deliveries return non-2xx and may reach the DLQ; there is no automatic stale-claim
recovery here. Investigate DB state before any manual recovery. Existing workflow
persistence may have partially succeeded before an exception; retrying the whole
workflow is not an exactly-once guarantee for those detailed entities.

## Per-user ordering (Step 11)

Both sides must enable ordering: the reusable Python publisher uses official
`PublisherOptions(enable_message_ordering=True)`, and the SOURCE subscription
must be created with `--enable-message-ordering` (included above). There is no
separate topic-level ordering switch. An existing subscription cannot have its
ordering property changed; plan a separately named replacement and a controlled
cutover during deployment, without deleting outstanding messages here.

The publisher passes the verified Clerk user ID as `ordering_key` metadata.
JSON remains exactly `{"job_id": "<uuid>"}`. The worker continues trusting Neon
for user identity. No key is accepted from client form/query/header fields.

Same-key messages follow Pub/Sub's regional publish order; different keys can
progress concurrently without a global user lock. Publish all messages for a key
in the same region. Keep publishers colocated in the chosen region; multi-region
publishing requires a deliberate locational-endpoint configuration at deployment.
Ordering is publish order, not job creation time or HTTP request arrival order;
concurrent publishers do not establish an independent business ordering.

Retries can delay later jobs for the same user until acknowledgment or eventual
DLQ forwarding. Other user keys can progress independently. Keep the atomic DB
claim: ordering does not eliminate duplicates. DLQ forwarding is best-effort and
ordering across dead-letter forwarding is not guaranteed. Do not treat this as
an exactly-once execution guarantee or a strict database-level per-user lock.

An unrecoverable ordered publish error can pause a key in the Python client;
operations should investigate and use the supported publisher resume mechanism
when safe. This step preserves the existing 503 and DB/GCS compensation behavior
and adds no automatic resume or republish workaround.

See [Google message ordering](https://docs.cloud.google.com/pubsub/docs/ordering)
and [publisher configuration](https://docs.cloud.google.com/pubsub/docs/publisher).
Unit tests verify configuration and keys, not actual remote delivery order.
All example commands remain documentation only; no resources were changed.
