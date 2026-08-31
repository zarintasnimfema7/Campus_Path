from app.models.plan import PlannerRequest
from app.models.workflow import WorkflowResult

from app.services.cv_analysis import (
    analyze_cv_text,
    extract_cv_text,
)
from app.services.job_analysis import analyze_job_description
from app.services.persistence import (
    save_job_target,
    save_learning_plan,
    save_skill_gap,
    save_student_profile,
)
from app.services.planner import generate_learning_plan
from app.services.skill_gap import analyze_skill_gap


async def run_initial_workflow(
    user_id: str,
    job_description: str,
    cv_filename: str,
    cv_bytes: bytes,
) -> WorkflowResult:

    # 1. Analyze target job.
    job = await analyze_job_description(
        job_description
    )

    # 2. Extract and analyze CV.
    cv_text = extract_cv_text(
        cv_filename,
        cv_bytes,
    )

    student = await analyze_cv_text(
        cv_text
    )

    # 3. Compare student with target job.
    skill_gap = await analyze_skill_gap(
        job,
        student,
    )

    # 4. Generate learning plan.
    planner_request = PlannerRequest(
        job=job,
        student=student,
        skill_gap=skill_gap,
    )

    plan = await generate_learning_plan(
        planner_request
    )

    # 5. Save job.
    saved_job = save_job_target(
        user_id=user_id,
        raw_description=job_description,
        job=job,
    )

    job_target_id = saved_job["id"]

    # 6. Save student profile.
    saved_profile = save_student_profile(
        user_id=user_id,
        profile=student,
    )

    # 7. Save skill assessments + readiness.
    save_skill_gap(
        user_id=user_id,
        job_target_id=job_target_id,
        skill_gap=skill_gap,
    )

    # 8. Save plan + tasks.
    saved_plan_data = save_learning_plan(
        user_id=user_id,
        job_target_id=job_target_id,
        plan=plan,
        readiness_score=skill_gap.readiness_score,
    )

    saved_plan = saved_plan_data["plan"]

    return WorkflowResult(
        user_id=user_id,
        job_target_id=job_target_id,
        profile_id=saved_profile["id"],
        plan_id=saved_plan["id"],
        job=job,
        student=student,
        skill_gap=skill_gap,
        plan=plan,
    )
