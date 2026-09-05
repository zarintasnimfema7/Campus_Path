"""Persistence for queued workflows using the existing Neon pool."""

from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from fastapi.encoders import jsonable_encoder

from app.database.neon import pool


def get_workflow_job_delivery_state(job_id: str) -> dict[str, Any] | None:
    """Internal lookup after a failed claim; never used to acquire ownership."""
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute('SELECT status, retry_count FROM workflow_jobs WHERE id = %s', (job_id,))
            return cursor.fetchone()


def record_workflow_job_failure(job_id: str, safe_error: str, max_retries: int) -> dict[str, Any] | None:
    """Atomically record a processing failure and requeue within the attempt cap."""
    if max_retries < 1:
        raise ValueError('Workflow attempt limit must be positive.')
    query = """
        UPDATE workflow_jobs
        SET retry_count = retry_count + 1,
            status = CASE WHEN retry_count + 1 >= %s THEN 'failed' ELSE 'queued' END,
            error = %s,
            updated_at = NOW(),
            completed_at = CASE WHEN retry_count + 1 >= %s THEN NOW() ELSE NULL END,
            started_at = CASE WHEN retry_count + 1 >= %s THEN started_at ELSE NULL END
        WHERE id = %s AND status = 'processing'
        RETURNING id, status, retry_count
    """
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, (max_retries, 'Workflow processing failed.', max_retries, max_retries, job_id))
            updated = cursor.fetchone()
        conn.commit()
    return updated


def get_workflow_job_for_user(job_id: str, user_id: str) -> dict[str, Any] | None:
    """Read only the polling fields for a job owned by the verified user."""
    query = """
        SELECT id, status, result, error, retry_count,
               created_at, updated_at, started_at, completed_at
        FROM workflow_jobs
        WHERE id = %s AND user_id = %s
    """
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, (job_id, user_id))
            return cursor.fetchone()


def mark_workflow_job_completed(job_id: str, result: Any) -> bool:
    """Persist the existing workflow result only while the job is processing."""
    query = """
        UPDATE workflow_jobs
        SET status = 'completed', result = %s, error = NULL,
            completed_at = NOW(), updated_at = NOW()
        WHERE id = %s AND status = 'processing'
        RETURNING id, status
    """
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (Jsonb(jsonable_encoder(result)), job_id))
            updated = cursor.fetchone()
        conn.commit()
    return updated is not None


def mark_workflow_job_failed(job_id: str, error: str) -> bool:
    """Store a fixed safe description rather than arbitrary exception details."""
    safe_error = 'Workflow processing failed.'
    query = """
        UPDATE workflow_jobs
        SET status = 'failed', error = %s,
            updated_at = NOW(), completed_at = NOW()
        WHERE id = %s AND status = 'processing'
        RETURNING id, status
    """
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (safe_error, job_id))
            updated = cursor.fetchone()
        conn.commit()
    return updated is not None


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
