from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.auth.dependencies import get_current_user
from app.models.replan import (
    ReplanRequest,
    ReplanResult,
)
from app.services.replanner import (
    replan_student,
)


router = APIRouter(
    prefix="/replan",
    tags=["Replanning"],
)


@router.post(
    "",
    response_model=ReplanResult,
)
async def replan(
    request: ReplanRequest,
    current_user=Depends(get_current_user),
):
    try:
        # JWT is verified before this endpoint runs.
        # This is the authenticated Supabase user ID.
        authenticated_user_id = current_user.id

        return await replan_student(
            request
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
                f"Replanning failed: {str(error)}"
            ),
        )