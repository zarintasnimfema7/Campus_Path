
from fastapi.encoders import jsonable_encoder
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.database.neon import pool
from app.services.ownership import require_job_owner, require_task_owner

from app.models.cv import CVAnalysisResult
from app.models.evidence import EvidenceVerificationResult
from app.models.job import JobAnalysisResult
from app.models.plan import LearningPlan
from app.models.skill_gap import SkillGapResult


def as_json(value):
    """Convert Python/Pydantic data into PostgreSQL JSONB."""
    return Jsonb(jsonable_encoder(value))


# =====================================================
# USER
# =====================================================

def create_user(
    user_id: str,
    name: str,
    email: str | None,
    github_username: str | None = None,
):

    query = """
        INSERT INTO users (
            id,
            name,
            email,
            github_username
        )
        VALUES (%s, %s, %s, %s)

        ON CONFLICT (id)
        DO UPDATE SET
            name = EXCLUDED.name,
            github_username = COALESCE(
                EXCLUDED.github_username,
                users.github_username
            ),
            updated_at = NOW()

        RETURNING
            id,
            name,
            email,
            github_username,
            created_at,
            updated_at;
    """

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                query,
                (
                    user_id,
                    name,
                    email,
                    github_username,
                ),
            )

            result = cursor.fetchone()

        conn.commit()

    return result


# =====================================================
# JOB TARGET
# =====================================================

def save_job_target(
    user_id: str,
    raw_description: str,
    job: JobAnalysisResult,
):
    query = """
        INSERT INTO job_targets (
            user_id,
            job_title,
            raw_description,
            required_skills,
            preferred_skills,
            experience,
            education,
            responsibilities
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s
        )

        RETURNING
            id::text AS id,
            user_id,
            job_title,
            created_at;
    """

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                query,
                (
                    user_id,
                    job.job_title,
                    raw_description,
                    as_json(job.required_skills),
                    as_json(job.preferred_skills),
                    as_json(job.experience),
                    as_json(job.education),
                    as_json(job.responsibilities),
                ),
            )

            result = cursor.fetchone()

        conn.commit()

    return result


# =====================================================
# STUDENT PROFILE
# =====================================================

def save_student_profile(
    user_id: str,
    profile: CVAnalysisResult,
):
    query = """
        INSERT INTO student_profiles (
            user_id,
            name,
            skills,
            education,
            projects,
            experience,
            certifications
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)

        RETURNING
            id::text AS id,
            user_id,
            name,
            created_at;
    """

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                query,
                (
                    user_id,
                    profile.name,
                    as_json(profile.skills),
                    as_json(profile.education),
                    as_json(profile.projects),
                    as_json(profile.experience),
                    as_json(profile.certifications),
                ),
            )

            result = cursor.fetchone()

        conn.commit()

    return result


# =====================================================
# SKILL GAP + READINESS
# =====================================================

def save_skill_gap(
    user_id: str,
    job_target_id: str,
    skill_gap: SkillGapResult,
):
    rows = []

    for assessment in skill_gap.required_assessments:
        rows.append(
            (
                user_id,
                job_target_id,
                assessment.skill,
                "required",
                assessment.status,
                as_json(assessment.evidence),
            )
        )

    for assessment in skill_gap.preferred_assessments:
        rows.append(
            (
                user_id,
                job_target_id,
                assessment.skill,
                "preferred",
                assessment.status,
                as_json(assessment.evidence),
            )
        )

    assessment_query = """
        INSERT INTO skill_assessments (
            user_id,
            job_target_id,
            skill,
            skill_type,
            status,
            evidence
        )
        VALUES (%s, %s, %s, %s, %s, %s);
    """

    readiness_query = """
        INSERT INTO readiness_history (
            user_id,
            job_target_id,
            readiness_score,
            required_score,
            preferred_score,
            reason
        )
        VALUES (%s, %s, %s, %s, %s, %s);
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            require_job_owner(cursor, job_target_id, user_id)

            if rows:
                cursor.executemany(
                    assessment_query,
                    rows,
                )

            cursor.execute(
                readiness_query,
                (
                    user_id,
                    job_target_id,
                    skill_gap.readiness_score,
                    skill_gap.required_score,
                    skill_gap.preferred_score,
                    "Initial skill gap analysis",
                ),
            )

        conn.commit()

    return {
        "saved_assessments": len(rows),
        "readiness_score": skill_gap.readiness_score,
    }


# =====================================================
# LEARNING PLAN + TASKS
# =====================================================

def save_learning_plan(
    user_id: str,
    job_target_id: str,
    plan: LearningPlan,
    readiness_score: float,
):
    plan_query = """
        INSERT INTO plans (
            user_id,
            job_target_id,
            title,
            summary,
            readiness_score
        )
        VALUES (%s, %s, %s, %s, %s)

        RETURNING
            id::text AS id,
            user_id,
            job_target_id::text AS job_target_id,
            title,
            summary,
            readiness_score,
            created_at;
    """

    task_query = """
        INSERT INTO tasks (
            plan_id,
            target_skill,
            title,
            goal,
            action,
            evidence_required,
            estimated_hours,
            priority,
            status
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )

        RETURNING
            id::text AS id,
            plan_id::text AS plan_id,
            target_skill,
            title,
            goal,
            action,
            estimated_hours,
            priority,
            status,
            created_at;
    """

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            require_job_owner(cursor, job_target_id, user_id)

            cursor.execute(
                plan_query,
                (
                    user_id,
                    job_target_id,
                    plan.plan_title,
                    plan.summary,
                    readiness_score,
                ),
            )

            saved_plan = cursor.fetchone()

            saved_tasks = []

            for task in plan.tasks:
                cursor.execute(
                    task_query,
                    (
                        saved_plan["id"],
                        task.target_skill,
                        task.title,
                        task.goal,
                        task.action,
                        as_json(task.evidence_required),
                        task.estimated_hours,
                        task.priority,
                        "pending",
                    ),
                )

                saved_tasks.append(
                    cursor.fetchone()
                )

        conn.commit()

    return {
        "plan": saved_plan,
        "tasks": saved_tasks,
    }


# =====================================================
# GITHUB EVIDENCE
# =====================================================

def save_evidence(
    task_id: str,
    verification: EvidenceVerificationResult,
    *, user_id: str,
):
    evidence_query = """
        INSERT INTO evidence (
            task_id,
            repository_url,
            verification_score,
            overall_status,
            checks,
            summary
        )
        VALUES (%s, %s, %s, %s, %s, %s)

        RETURNING
            id::text AS id,
            task_id::text AS task_id,
            repository_url,
            verification_score,
            overall_status,
            checks,
            summary,
            created_at;
    """

    update_task_query = """
        UPDATE tasks
        SET
            status = %s,
            updated_at = NOW()
        WHERE id = %s AND plan_id IN (SELECT id FROM plans WHERE user_id = %s);
    """

    if verification.overall_status == "verified":
        task_status = "verified"
    else:
        task_status = "completed"

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            require_task_owner(cursor, task_id, user_id)

            cursor.execute(
                evidence_query,
                (
                    task_id,
                    verification.repository_url,
                    verification.verification_score,
                    verification.overall_status,
                    as_json(verification.checks),
                    verification.summary,
                ),
            )

            saved_evidence = cursor.fetchone()

            cursor.execute(
                update_task_query,
                (
                    task_status,
                    task_id,
                    user_id,
                ),
            )

        conn.commit()

    return saved_evidence


# =====================================================
# ACTIVITY LOG
# =====================================================

def log_activity(
    user_id: str,
    action: str,
    details: dict | None = None,
):
    query = """
        INSERT INTO activity_logs (
            user_id,
            action,
            details
        )
        VALUES (%s, %s, %s);
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    user_id,
                    action,
                    as_json(details or {}),
                ),
            )

        conn.commit()


# =====================================================
# AGENT RUN LOG
# =====================================================

def log_agent_run(
    user_id: str,
    agent_name: str,
    input_data: dict,
    output_data: dict,
    status: str = "completed",
):
    query = """
        INSERT INTO agent_runs (
            user_id,
            agent_name,
            status,
            input_data,
            output_data
        )
        VALUES (%s, %s, %s, %s, %s);
    """

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    user_id,
                    agent_name,
                    status,
                    as_json(input_data),
                    as_json(output_data),
                ),
            )

        conn.commit()