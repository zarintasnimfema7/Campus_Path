from app.database.supabase import supabase

from app.models.cv import CVAnalysisResult
from app.models.evidence import EvidenceVerificationResult
from app.models.job import JobAnalysisResult
from app.models.plan import LearningPlan
from app.models.skill_gap import SkillGapResult


def create_user(
    name: str,
    email: str,
    github_username: str | None = None,
):
    response = (
        supabase
        .table("users")
        .insert(
            {
                "name": name,
                "email": email,
                "github_username": github_username,
            }
        )
        .execute()
    )

    return response.data[0]


def save_job_target(
    user_id: str,
    raw_description: str,
    job: JobAnalysisResult,
):
    response = (
        supabase
        .table("job_targets")
        .insert(
            {
                "user_id": user_id,
                "job_title": job.job_title,
                "raw_description": raw_description,
                "required_skills": job.required_skills,
                "preferred_skills": job.preferred_skills,
                "experience": job.experience,
                "education": job.education,
                "responsibilities": job.responsibilities,
            }
        )
        .execute()
    )

    return response.data[0]


def save_student_profile(
    user_id: str,
    profile: CVAnalysisResult,
):
    response = (
        supabase
        .table("student_profiles")
        .insert(
            {
                "user_id": user_id,
                "name": profile.name,
                "skills": profile.skills,
                "education": [
                    item.model_dump()
                    for item in profile.education
                ],
                "projects": [
                    item.model_dump()
                    for item in profile.projects
                ],
                "experience": [
                    item.model_dump()
                    for item in profile.experience
                ],
                "certifications": profile.certifications,
            }
        )
        .execute()
    )

    return response.data[0]


def save_skill_gap(
    user_id: str,
    job_target_id: str,
    skill_gap: SkillGapResult,
):

    rows = []

    for assessment in skill_gap.required_assessments:
        rows.append(
            {
                "user_id": user_id,
                "job_target_id": job_target_id,
                "skill": assessment.skill,
                "skill_type": "required",
                "status": assessment.status,
                "evidence": assessment.evidence,
            }
        )

    for assessment in skill_gap.preferred_assessments:
        rows.append(
            {
                "user_id": user_id,
                "job_target_id": job_target_id,
                "skill": assessment.skill,
                "skill_type": "preferred",
                "status": assessment.status,
                "evidence": assessment.evidence,
            }
        )

    if rows:
        (
            supabase
            .table("skill_assessments")
            .insert(rows)
            .execute()
        )

    (
        supabase
        .table("readiness_history")
        .insert(
            {
                "user_id": user_id,
                "job_target_id": job_target_id,
                "readiness_score": skill_gap.readiness_score,
                "required_score": skill_gap.required_score,
                "preferred_score": skill_gap.preferred_score,
                "reason": "Initial skill gap analysis",
            }
        )
        .execute()
    )

    return {
        "saved_assessments": len(rows),
        "readiness_score": skill_gap.readiness_score,
    }


def save_learning_plan(
    user_id: str,
    job_target_id: str,
    plan: LearningPlan,
    readiness_score: float,
):

    plan_response = (
        supabase
        .table("plans")
        .insert(
            {
                "user_id": user_id,
                "job_target_id": job_target_id,
                "title": plan.plan_title,
                "summary": plan.summary,
                "readiness_score": readiness_score,
            }
        )
        .execute()
    )

    saved_plan = plan_response.data[0]

    plan_id = saved_plan["id"]

    task_rows = []

    for task in plan.tasks:
        task_rows.append(
            {
                "plan_id": plan_id,
                "target_skill": task.target_skill,
                "title": task.title,
                "goal": task.goal,
                "action": task.action,
                "evidence_required": task.evidence_required,
                "estimated_hours": task.estimated_hours,
                "priority": task.priority,
                "status": "pending",
            }
        )

    saved_tasks = []

    if task_rows:
        task_response = (
            supabase
            .table("tasks")
            .insert(task_rows)
            .execute()
        )

        saved_tasks = task_response.data

    return {
        "plan": saved_plan,
        "tasks": saved_tasks,
    }


def save_evidence(
    task_id: str,
    verification: EvidenceVerificationResult,
):

    response = (
        supabase
        .table("evidence")
        .insert(
            {
                "task_id": task_id,
                "repository_url": verification.repository_url,
                "verification_score": verification.verification_score,
                "overall_status": verification.overall_status,
                "checks": [
                    check.model_dump()
                    for check in verification.checks
                ],
                "summary": verification.summary,
            }
        )
        .execute()
    )

    # Update task status.
    if verification.overall_status == "verified":
        task_status = "verified"
    else:
        task_status = "completed"

    (
        supabase
        .table("tasks")
        .update(
            {
                "status": task_status
            }
        )
        .eq(
            "id",
            task_id,
        )
        .execute()
    )

    return response.data[0]


def log_activity(
    user_id: str,
    action: str,
    details: dict | None = None,
):

    (
        supabase
        .table("activity_logs")
        .insert(
            {
                "user_id": user_id,
                "action": action,
                "details": details or {},
            }
        )
        .execute()
    )


def log_agent_run(
    user_id: str,
    agent_name: str,
    input_data: dict,
    output_data: dict,
    status: str = "completed",
):

    (
        supabase
        .table("agent_runs")
        .insert(
            {
                "user_id": user_id,
                "agent_name": agent_name,
                "status": status,
                "input_data": input_data,
                "output_data": output_data,
            }
        )
        .execute()
    )
