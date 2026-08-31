from fastapi import (
    APIRouter,
    HTTPException,
)

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
):

    try:

        return await replan_student(
            request
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
                f"Replanning failed: {str(error)}"
            ),
        )
