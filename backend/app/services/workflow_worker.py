"""Internal synchronous worker; call from a worker thread, not an event loop."""

import asyncio

from app.models.workflow import WorkflowResult
from app.services.storage import download_cv
from app.services.workflow_jobs import claim_workflow_job


def process_workflow_job(job_id: str) -> WorkflowResult | None:
    """Claim first, then process trusted DB inputs outside the claim transaction."""
    job = claim_workflow_job(job_id)
    if job is None:
        return None
    object_path = job.get('cv_object_path')
    if not object_path:
        raise RuntimeError('Claimed workflow job has no CV object path.')
    cv_bytes = download_cv(object_path)

    # Load the existing AI workflow only after acquiring the job. Its synchronous
    # extraction/persistence and async AI calls stay off the HTTP event loop.
    from app.services.workflow import run_initial_workflow

    return asyncio.run(run_initial_workflow(
        user_id=job['user_id'],
        job_description=job['job_description'],
        cv_filename=object_path.rsplit('/', 1)[-1],
        cv_bytes=cv_bytes,
    ))
