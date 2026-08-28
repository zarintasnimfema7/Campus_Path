from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from app.models.cv import CVAnalysisResult
from app.services.cv_analysis import (
    analyze_cv_text,
    extract_cv_text,
)


router = APIRouter(
    prefix="/cv",
    tags=["CV"],
)


MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post(
    "/analyze",
    response_model=CVAnalysisResult,
)
async def analyze_cv(
    file: UploadFile = File(...),
):

    try:
        if not file.filename:
            raise ValueError(
                "The uploaded file must have a filename."
            )

        allowed_extensions = (
            ".pdf",
            ".docx",
        )

        if not file.filename.lower().endswith(
            allowed_extensions
        ):
            raise ValueError(
                "Only PDF and DOCX CV files are supported."
            )

        file_bytes = await file.read()

        if len(file_bytes) > MAX_FILE_SIZE:
            raise ValueError(
                "CV file must be smaller than 5 MB."
            )

        cv_text = extract_cv_text(
            file.filename,
            file_bytes,
        )

        result = await analyze_cv_text(cv_text)

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"CV analysis failed: {str(error)}",
        )
