from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from app.auth.dependencies import get_current_user
from app.models.workflow import WorkflowResult
from app.services.user_services import ensure_user_exists
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
    job_description: str = Form(...),
    cv: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    user_id = current_user.id
    user_email = current_user.email

    user_name = None

    if current_user.user_metadata:
        user_name = current_user.user_metadata.get(
            "full_name"
        )

    ensure_user_exists(
        user_id=user_id,
        email=user_email,
        name=user_name,
    )

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

    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="CV must be 5 MB or smaller.",
        )

    if not job_description.strip():
        raise HTTPException(
            status_code=400,
            detail="Job description is required.",
        )

    try:
        return await run_initial_workflow(
            user_id=user_id,
            job_description=job_description.strip(),
            cv_filename=cv.filename,
            cv_bytes=file_bytes,
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
            detail=str(error),
        )