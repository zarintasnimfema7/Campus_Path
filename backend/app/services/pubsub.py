"""Publish job identifiers using ADC and a lazily reused publisher."""

from functools import lru_cache
import json
import os
from uuid import UUID

from google.cloud import pubsub_v1


@lru_cache(maxsize=1)
def _publisher() -> pubsub_v1.PublisherClient:
    return pubsub_v1.PublisherClient(
        publisher_options=pubsub_v1.types.PublisherOptions(enable_message_ordering=True),
    )


def publish_workflow_job(job_id: str, ordering_key: str) -> str:
    """Block until Pub/Sub acknowledges the message, then return its message ID."""
    if not isinstance(ordering_key, str) or not ordering_key.strip():
        raise ValueError('A nonempty authenticated user ordering key is required.')
    project = os.environ.get('GOOGLE_CLOUD_PROJECT', '').strip()
    topic = os.environ.get('PUBSUB_TOPIC_ID', '').strip()
    if not project or not topic:
        raise RuntimeError('GOOGLE_CLOUD_PROJECT and PUBSUB_TOPIC_ID must be configured to publish jobs.')
    payload = json.dumps({'job_id': str(UUID(job_id))}).encode('utf-8')
    publisher = _publisher()
    topic_path = publisher.topic_path(project, topic)
    future = publisher.publish(topic_path, data=payload, ordering_key=ordering_key)
    return future.result()
