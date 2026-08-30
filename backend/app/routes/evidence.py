from fastapi import (
    APIRouter,
    HTTPException,
)

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
):

    try:

        return await verify_repository_evidence(
            repository_url=request.repository_url,
            task=request.task,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Evidence verification failed: "
                f"{str(error)}"
            ),
        )
