from fastapi import Depends
from app.auth.dependencies import get_current_user
from fastapi import (
    APIRouter,
    HTTPException,
)

from app.models.plan import (
    LearningPlan,
    PlannerRequest,
)

from app.services.planner import (
    generate_learning_plan,
)


router = APIRouter(
    prefix="/planner",
    tags=["Planner"],
)


@router.post(
    "/generate",
    response_model=LearningPlan,
)
async def create_learning_plan(
    request: PlannerRequest,
    current_user=Depends(get_current_user),
):

    try:

        return await generate_learning_plan(
            request
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail="Analysis is temporarily unavailable.",
        )
