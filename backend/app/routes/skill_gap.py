from fastapi import (
    APIRouter,
    HTTPException,
)

from app.models.skill_gap import (
    SkillGapRequest,
    SkillGapResult,
)

from app.services.skill_gap import (
    analyze_skill_gap,
)


router = APIRouter(
    prefix="/skill-gap",
    tags=["Skill Gap"],
)


@router.post(
    "/analyze",
    response_model=SkillGapResult,
)
async def analyze_gap(
    request: SkillGapRequest,
):

    try:

        result = await analyze_skill_gap(
            job=request.job,
            student=request.student,
        )

        return result

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Skill gap analysis failed: "
                f"{str(error)}"
            ),
        )
