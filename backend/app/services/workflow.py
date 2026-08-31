from app.models.plan import PlannerRequest
from app.models.workflow import WorkflowResult

from app.services.cv_analysis import extract_cv_text
from app.services.combined_analysis import (
    analyze_job_and_cv,
)
from app.services.persistence import (
    save_job_target,
    save_learning_plan,
    save_skill_gap,
    save_student_profile,
)
from app.services.planner import (
    generate_learning_plan,
)
from app.services.skill_gap import (
    analyze_skill_gap,
)


async def run_initial_workflow(
    user_id: str,
    job_description: str,
    cv_filename: str,
    cv_bytes: bytes,
) -> WorkflowResult:

    # -------------------------------------------------
    # 1. Extract CV text locally
    # No Gemini call here.
    # -------------------------------------------------

    cv_text = extract_cv_text(
        cv_filename,
        cv_bytes,
    )

    # -------------------------------------------------
    # 2. Analyze job + CV together
    # GEMINI CALL #1
    # -------------------------------------------------

    combined_analysis = (
        await analyze_job_and_cv(
            job_description=job_description,
            cv_text=cv_text,
        )
    )

    job = combined_analysis.job
    student = combined_analysis.student

    # -------------------------------------------------
    # 3. Skill gap analysis
    # Python/deterministic.
    # No Gemini call.
    # -------------------------------------------------

    skill_gap = await analyze_skill_gap(
        job,
        student,
    )

    # -------------------------------------------------
    # 4. Generate learning plan
    # GEMINI CALL #2
    # -------------------------------------------------

    planner_request = PlannerRequest(
        job=job,
        student=student,
        skill_gap=skill_gap,
    )

    plan = await generate_learning_plan(
        planner_request
    )

    # -------------------------------------------------
    # 5. Save target job
    # -------------------------------------------------

    saved_job = save_job_target(
        user_id=user_id,
        raw_description=job_description,
        job=job,
    )

    job_target_id = saved_job["id"]

    # -------------------------------------------------
    # 6. Save student profile
    # -------------------------------------------------

    saved_profile = save_student_profile(
        user_id=user_id,
        profile=student,
    )

    # -------------------------------------------------
    # 7. Save skill assessments/readiness
    # -------------------------------------------------

    save_skill_gap(
        user_id=user_id,
        job_target_id=job_target_id,
        skill_gap=skill_gap,
    )

    # -------------------------------------------------
    # 8. Save plan and learning tasks
    # -------------------------------------------------

    saved_plan_data = save_learning_plan(
        user_id=user_id,
        job_target_id=job_target_id,
        plan=plan,
        readiness_score=(
            skill_gap.readiness_score
        ),
    )

    saved_plan = saved_plan_data["plan"]

    # -------------------------------------------------
    # 9. Return complete workflow result
    # -------------------------------------------------

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