"""Persistence for queued workflows using the existing Neon pool."""

from app.database.neon import pool


def create_workflow_job(
    job_id: str,
    user_id: str,
    job_description: str,
    target_role: str | None,
    cv_object_path: str,
) -> None:
    query = """
        INSERT INTO workflow_jobs (
            id, user_id, job_description, target_role, cv_object_path, status
        )
        VALUES (%s, %s, %s, %s, %s, 'queued')
    """
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (job_id, user_id, job_description, target_role, cv_object_path),
            )
        conn.commit()
