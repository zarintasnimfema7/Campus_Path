import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.auth.dependencies import get_current_user
from app.models.workflow import WorkflowQueuedResponse, WorkflowStatusResponse
from app.services.storage import delete_cv, upload_cv
from app.services.user_services import ensure_user_exists
from app.services.workflow_jobs import create_workflow_job, delete_workflow_job
from app.services.pubsub import publish_workflow_job
from app.services.workflow_jobs import get_workflow_job_for_user


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflow", tags=["Workflow"])


@router.get('/{job_id}', response_model=WorkflowStatusResponse)
def get_workflow_status(job_id: UUID, current_user=Depends(get_current_user)):
    try:
        job = get_workflow_job_for_user(str(job_id), current_user['id'])
    except Exception as error:
        logger.error('Workflow status lookup failed (%s).', type(error).__name__)
        raise HTTPException(status_code=503, detail='Workflow status is temporarily unavailable.') from None
    if job is None:
        raise HTTPException(status_code=404, detail='Workflow job not found.')
    return WorkflowStatusResponse(
        job_id=job['id'], status=job['status'], retry_count=job['retry_count'],
        result=job['result'] if job['status'] == 'completed' else None,
        error='Workflow processing failed.' if job['status'] == 'failed' else None,
        created_at=job['created_at'], updated_at=job['updated_at'],
        started_at=job['started_at'], completed_at=job['completed_at'],
    )


@router.post("/start", response_model=WorkflowQueuedResponse, status_code=202)
def start_workflow(
    job_description: str = Form(...),
    cv: UploadFile = File(...),
    target_role: str | None = Form(None),
    current_user=Depends(get_current_user),
):
    # This sync handler runs blocking storage/psycopg work in FastAPI's thread pool.
    user_id = current_user["id"]
    job_description = job_description.strip()
    if not job_description:
        raise HTTPException(status_code=400, detail="Job description is required.")
    target_role = (target_role.strip() or None) if target_role is not None else None
    job_id = str(uuid4())

    try:
        cv_object_path = upload_cv(file=cv, user_id=user_id, job_id=job_id)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid CV. Upload a nonempty PDF, DOC, or DOCX of 5 MiB or smaller with a matching content type.",
        ) from error
    except Exception as error:
        logger.error("CV upload failed (%s).", type(error).__name__)
        raise HTTPException(status_code=503, detail="CV storage is temporarily unavailable.") from error

    try:
        ensure_user_exists(
            user_id=user_id,
            email=current_user.get("email"),
            name=current_user.get("name"),
        )
        create_workflow_job(
            job_id=job_id,
            user_id=user_id,
            job_description=job_description,
            target_role=target_role,
            cv_object_path=cv_object_path,
        )
    except Exception as error:
        # Keep the original DB failure even if best-effort object cleanup fails.
        logger.error("Workflow job persistence failed (%s).", type(error).__name__)
        try:
            delete_cv(cv_object_path)
        except Exception as cleanup_error:
            logger.error("CV cleanup failed (%s).", type(cleanup_error).__name__)
        raise HTTPException(status_code=503, detail="Could not create workflow job. Please try again.") from error

    try:
        publish_workflow_job(job_id)
    except Exception as error:
        logger.error("Workflow publish failed for job %s (%s).", job_id, type(error).__name__)
        try:
            delete_workflow_job(job_id, user_id)
        except Exception as cleanup_error:
            logger.error("Workflow job cleanup failed (%s).", type(cleanup_error).__name__)
        try:
            delete_cv(cv_object_path)
        except Exception as cleanup_error:
            logger.error("CV cleanup failed (%s).", type(cleanup_error).__name__)
        raise HTTPException(status_code=503, detail="Could not publish workflow job. Please try again.") from error

    return WorkflowQueuedResponse(job_id=job_id, status="queued")
