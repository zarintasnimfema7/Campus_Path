"""Internal synchronous worker; call from a worker thread, not an event loop."""

import asyncio
import logging
import os

from app.models.workflow import WorkflowResult
from app.services.storage import download_cv
from app.services.workflow_jobs import (
    claim_workflow_job,
    mark_workflow_job_completed,
    record_workflow_job_failure,
    get_workflow_job_delivery_state,
)

logger = logging.getLogger(__name__)


def workflow_max_retries() -> int:
    """Total processing-attempt cap, including the initial attempt."""
    try:
        value = int(os.environ.get('WORKFLOW_MAX_RETRIES', '5'))
        return value if value > 0 else 5
    except ValueError:
        return 5


def process_workflow_job(job_id: str) -> WorkflowResult | None:
    """Claim first, then process trusted DB inputs outside the claim transaction."""
    max_retries = workflow_max_retries()
    job = claim_workflow_job(job_id)
    if job is None:
        state = get_workflow_job_delivery_state(job_id)
        if state is None or state['status'] == 'completed':
            return None
        # Do not ACK concurrent processing, a requeue race, or a terminal failed
        # message that still needs unsuccessful deliveries for DLQ forwarding.
        raise RuntimeError('Workflow delivery is not ready to be acknowledged.')
    try:
        object_path = job.get('cv_object_path')
        if not object_path:
            raise RuntimeError('Claimed workflow job has no CV object path.')
        cv_bytes = download_cv(object_path)

        from app.services.workflow import run_initial_workflow

        result = asyncio.run(run_initial_workflow(
            user_id=job['user_id'],
            job_description=job['job_description'],
            cv_filename=object_path.rsplit('/', 1)[-1],
            cv_bytes=cv_bytes,
        ))
    except Exception:
        try:
            if not record_workflow_job_failure(job_id, 'Workflow processing failed.', max_retries):
                logger.error('Workflow failure state was not updated for job %s.', job_id)
        except Exception as update_error:
            logger.error('Workflow failure state update failed (%s).', type(update_error).__name__)
        raise

    # Completion persistence errors propagate without rerunning AI or replacing
    # a potentially committed final state with failed.
    if not mark_workflow_job_completed(job_id, result):
        raise RuntimeError('Workflow completion state was not updated.')
    return result
