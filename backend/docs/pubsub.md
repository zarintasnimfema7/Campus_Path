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
No application retry loops, manual republishing, or ordering are implemented.

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
gcloud pubsub subscriptions create <SOURCE_SUBSCRIPTION> --project=<PROJECT_ID> --topic=<MAIN_TOPIC> --push-endpoint=<WORKER_BASE_URL>/internal/workflow-jobs/process --push-auth-service-account=<PUSH_SERVICE_ACCOUNT_EMAIL> --push-auth-token-audience=<WORKER_BASE_URL> --dead-letter-topic=projects/<PROJECT_ID>/topics/<DLQ_TOPIC> --max-delivery-attempts=5 --ack-deadline=600 --min-retry-delay=10s --max-retry-delay=60s
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
