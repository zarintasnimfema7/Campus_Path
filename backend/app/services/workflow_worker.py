"""Internal synchronous worker; call from a worker thread, not an event loop."""

import asyncio
import logging

from app.models.workflow import WorkflowResult
from app.services.storage import download_cv
from app.services.workflow_jobs import (
    claim_workflow_job,
    mark_workflow_job_completed,
    mark_workflow_job_failed,
)

logger = logging.getLogger(__name__)


def process_workflow_job(job_id: str) -> WorkflowResult | None:
    """Claim first, then process trusted DB inputs outside the claim transaction."""
    job = claim_workflow_job(job_id)
    if job is None:
        return None
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
            if not mark_workflow_job_failed(job_id, 'Workflow processing failed.'):
                logger.error('Workflow failure state was not updated for job %s.', job_id)
        except Exception as update_error:
            logger.error('Workflow failure state update failed (%s).', type(update_error).__name__)
        raise

    # Completion persistence errors propagate without rerunning AI or replacing
    # a potentially committed final state with failed.
    if not mark_workflow_job_completed(job_id, result):
        raise RuntimeError('Workflow completion state was not updated.')
    return result
