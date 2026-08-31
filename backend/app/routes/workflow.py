from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from app.models.workflow import WorkflowResult
from app.services.workflow import run_initial_workflow


router = APIRouter(
    prefix="/workflow",
    tags=["Workflow"],
)


@router.post(
    "/start",
    response_model=WorkflowResult,
)
async def start_workflow(
    user_id: str = Form(...),
    job_description: str = Form(...),
    cv: UploadFile = File(...),
):

    if not cv.filename:
        raise HTTPException(
            status_code=400,
            detail="CV filename is missing.",
        )

    filename = cv.filename.lower()

    if not (
        filename.endswith(".pdf")
        or filename.endswith(".docx")
    ):
        raise HTTPException(
            status_code=400,
            detail="CV must be a PDF or DOCX file.",
        )

    file_bytes = await cv.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded CV is empty.",
        )

    # Same 5 MB limit used by the CV feature.
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="CV must be 5 MB or smaller.",
        )

    try:

        return await run_initial_workflow(
            user_id=user_id,
            job_description=job_description,
            cv_filename=cv.filename,
            cv_bytes=file_bytes,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )
