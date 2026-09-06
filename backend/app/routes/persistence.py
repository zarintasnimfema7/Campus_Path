from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_user
from app.services.access_logs import log_access_event

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
    current_user=Depends(get_current_user),
):

    try:
        result = create_user(
            current_user["id"],
            request.name,
            current_user.get("email"),
            request.github_username,
        )
        log_access_event(current_user["id"], "profile_updated", "profile")
        return result

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not save the requested data.",
        )


@router.post("/jobs")
def save_job_route(
    request: SaveJobRequest,
    current_user=Depends(get_current_user),
):

    try:
        result = save_job_target(
            current_user["id"],
            request.raw_description,
            request.job,
        )
        log_access_event(current_user["id"], "job_saved", "job")
        return result

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not save the requested data.",
        )


@router.post("/profiles")
def save_profile_route(
    request: SaveProfileRequest,
    current_user=Depends(get_current_user),
):

    try:
        result = save_student_profile(
            current_user["id"],
            request.profile,
        )
        log_access_event(current_user["id"], "profile_updated", "profile")
        return result

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not save the requested data.",
        )


@router.post("/skill-gaps")
def save_skill_gap_route(
    request: SaveSkillGapRequest,
    current_user=Depends(get_current_user),
):

    try:
        result = save_skill_gap(
            current_user["id"],
            request.job_target_id,
            request.skill_gap,
        )
        log_access_event(current_user["id"], "skill_gap_saved", "skill_gap")
        return result

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not save the requested data.",
        )


@router.post("/plans")
def save_plan_route(
    request: SavePlanRequest,
    current_user=Depends(get_current_user),
):

    try:
        result = save_learning_plan(
            current_user["id"],
            request.job_target_id,
            request.plan,
            request.readiness_score,
        )
        log_access_event(current_user["id"], "plan_saved", "plan")
        return result

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not save the requested data.",
        )


@router.post("/evidence")
def save_evidence_route(
    request: SaveEvidenceRequest,
    current_user=Depends(get_current_user),
):

    try:
        result = save_evidence(
            request.task_id,
            request.verification,
            user_id=current_user["id"],
        )
        log_access_event(current_user["id"], "evidence_submitted", "evidence")
        return result

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not save the requested data.",
        )
