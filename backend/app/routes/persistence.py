from fastapi import APIRouter, HTTPException

from app.models.persistence import (
    CreateUserRequest,
    SaveEvidenceRequest,
    SaveJobRequest,
    SavePlanRequest,
    SaveProfileRequest,
    SaveSkillGapRequest,
)

from app.services.persistence import (
    create_user,
    save_evidence,
    save_job_target,
    save_learning_plan,
    save_skill_gap,
    save_student_profile,
)


router = APIRouter(
    prefix="/data",
    tags=["Persistence"],
)


@router.post("/users")
def create_user_route(
    request: CreateUserRequest,
):

    try:
        return create_user(
            request.name,
            request.email,
            request.github_username,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@router.post("/jobs")
def save_job_route(
    request: SaveJobRequest,
):

    try:
        return save_job_target(
            request.user_id,
            request.raw_description,
            request.job,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@router.post("/profiles")
def save_profile_route(
    request: SaveProfileRequest,
):

    try:
        return save_student_profile(
            request.user_id,
            request.profile,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@router.post("/skill-gaps")
def save_skill_gap_route(
    request: SaveSkillGapRequest,
):

    try:
        return save_skill_gap(
            request.user_id,
            request.job_target_id,
            request.skill_gap,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@router.post("/plans")
def save_plan_route(
    request: SavePlanRequest,
):

    try:
        return save_learning_plan(
            request.user_id,
            request.job_target_id,
            request.plan,
            request.readiness_score,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@router.post("/evidence")
def save_evidence_route(
    request: SaveEvidenceRequest,
):

    try:
        return save_evidence(
            request.task_id,
            request.verification,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )
