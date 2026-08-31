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
        # The JWT has already been verified by get_current_user().
        # current_user.id is now the authenticated Supabase user ID.
        authenticated_user_id = current_user.id

        return await verify_repository_evidence(
            repository_url=request.repository_url,
            task=request.task,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Evidence verification failed: "
                f"{str(error)}"
            ),
        )