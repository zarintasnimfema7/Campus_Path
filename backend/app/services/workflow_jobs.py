"""Persistence for queued workflows using the existing Neon pool."""

from typing import Any

from psycopg.rows import dict_row

from app.database.neon import pool


def claim_workflow_job(job_id: str) -> dict[str, Any] | None:
    """Claim a queued job, committing and releasing its connection before return.

    None means this caller did not acquire the job. Processing happens later,
    outside this short transaction, using the trusted data returned by Neon.
    """
    query = """
        UPDATE workflow_jobs
        SET status = 'processing',
            started_at = NOW(),
            updated_at = NOW()
        WHERE id = %s AND status = 'queued'
        RETURNING id, user_id, target_role, job_description, cv_object_path,
                  status, retry_count, created_at, updated_at, started_at,
                  completed_at
    """
    try:
        with pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(query, (job_id,))
                job = cursor.fetchone()
            conn.commit()
    except Exception:
        # Driver errors may contain connection details. The pool context rolls
        # back failed transactions; never report ownership after a DB failure.
        raise RuntimeError('Could not claim workflow job.') from None
    return job


def delete_workflow_job(job_id: str, user_id: str) -> None:
    """Compensate a failed publish, scoped to this job and authenticated user."""
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'DELETE FROM workflow_jobs WHERE id = %s AND user_id = %s',
                (job_id, user_id),
            )
        conn.commit()


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
