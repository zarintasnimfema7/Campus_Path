from app.services.access_logs import log_access_event
from app.services.ownership import get_task_for_user
from starlette.concurrency import run_in_threadpool
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.auth.dependencies import get_current_user
from app.models.evidence import (
    EvidenceVerificationRequest,
    EvidenceVerificationResult,
)
from app.services.evidence_verifier import (
    verify_repository_evidence,
)


router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"],
)


@router.post(
    "/verify-github",
    response_model=EvidenceVerificationResult,
)
async def verify_github_evidence(
    request: EvidenceVerificationRequest,
    current_user=Depends(get_current_user),
):
    try:
        # The JWT has already been verified by get_current_user()
        authenticated_user_id = current_user["id"]
        task = request.task
        if request.task_id is not None:
            task = await run_in_threadpool(get_task_for_user, request.task_id, authenticated_user_id)

        result = await verify_repository_evidence(
            repository_url=request.repository_url,
            task=task,
        )
        await run_in_threadpool(log_access_event, authenticated_user_id, "evidence_verified", "task", request.task_id)
        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail="The supplied analysis input is invalid.",
        )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Analysis is temporarily unavailable.",
        )
