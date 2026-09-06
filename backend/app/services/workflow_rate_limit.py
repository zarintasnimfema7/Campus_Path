"""Cross-instance sliding-window admission, committed before any external work."""
import hashlib
import os

from app.database.neon import pool
from app.services.access_logs import insert_access_event


def positive_setting(name, default):
    value = int(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError('Rate limit settings must be positive integers')
    return value


def reserve_workflow_start(user_id):
    limit = positive_setting('WORKFLOW_START_RATE_LIMIT', 5)
    window = positive_setting('WORKFLOW_START_RATE_WINDOW_SECONDS', 600)
    key = int.from_bytes(hashlib.sha256(('workflow-start:' + user_id).encode()).digest()[:8], 'big', signed=True)
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            # Explicit isolation gives a fresh snapshot after a competing admission commits.
            cursor.execute('SET TRANSACTION ISOLATION LEVEL READ COMMITTED')
            cursor.execute('SELECT pg_advisory_xact_lock(%s)', (key,))
            cursor.execute('''
                SELECT count(*) FROM access_logs
                WHERE user_id = %s AND action = 'workflow_start_reserved'
                  AND created_at > clock_timestamp() - (%s * interval '1 second')
            ''', (user_id, window))
            allowed = cursor.fetchone()[0] < limit
            insert_access_event(cursor, user_id,
                                'workflow_start_reserved' if allowed else 'workflow_start_rate_limited',
                                'workflow', outcome='reserved' if allowed else 'denied')
        conn.commit()
    return allowed
