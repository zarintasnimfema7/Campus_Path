from fastapi import Depends
from app.auth.dependencies import get_current_user
from fastapi import APIRouter, HTTPException

from app.models.job import (
    JobAnalysisRequest,
    JobAnalysisResult,
)
from app.services.job_analysis import analyze_job_description


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.post(
    "/analyze",
    response_model=JobAnalysisResult,
)
async def analyze_job(request: JobAnalysisRequest, current_user=Depends(get_current_user)):

    try:
        result = await analyze_job_description(
            request.job_description
        )

        return result

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Analysis is temporarily unavailable."
        )
