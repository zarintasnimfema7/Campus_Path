from uuid import UUID
from fastapi import HTTPException
from psycopg.rows import dict_row
from app.database.neon import pool
from app.models.plan import LearningTask


def resource_uuid(value):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=404, detail='Resource not found.') from None


def require_job_owner(cursor, job_id, user_id):
    cursor.execute('SELECT id FROM job_targets WHERE id = %s AND user_id = %s FOR SHARE',
                   (resource_uuid(job_id), user_id))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail='Resource not found.')


def require_task_owner(cursor, task_id, user_id):
    cursor.execute('''
        SELECT t.id FROM tasks t JOIN plans p ON p.id = t.plan_id
        WHERE t.id = %s AND p.user_id = %s FOR UPDATE OF t, p
    ''', (resource_uuid(task_id), user_id))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail='Resource not found.')


def get_task_for_user(task_id, user_id):
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute('''
                SELECT t.title, t.target_skill, t.goal, t.action,
                       t.evidence_required, t.estimated_hours, t.priority
                FROM tasks t JOIN plans p ON p.id = t.plan_id
                WHERE t.id = %s AND p.user_id = %s
            ''', (resource_uuid(task_id), user_id))
            task = cursor.fetchone()
    if task is None:
        raise HTTPException(status_code=404, detail='Resource not found.')
    return LearningTask.model_validate(task)
