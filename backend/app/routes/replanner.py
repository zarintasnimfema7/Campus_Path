from app.services.access_logs import log_access_event
from starlette.concurrency import run_in_threadpool
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
        
        authenticated_user_id = current_user["id"]

        result = await replan_student(
            request
        )
        await run_in_threadpool(log_access_event, authenticated_user_id, "plan_replanned", "plan")
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
