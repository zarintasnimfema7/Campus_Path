"""Small allowlisted events; never accept request bodies as audit metadata."""
import logging
from uuid import UUID

from psycopg.types.json import Jsonb
from app.database.neon import pool

logger = logging.getLogger(__name__)
ACTIONS = frozenset({
    'workflow_start_reserved', 'workflow_start_accepted', 'workflow_start_rate_limited',
    'evidence_submitted', 'evidence_verified', 'plan_replanned', 'profile_updated',
    'job_saved', 'plan_saved', 'skill_gap_saved',
})


def insert_access_event(cursor, user_id, action, resource_type=None, resource_id=None,
                        outcome='success', metadata=None):
    if action not in ACTIONS or outcome not in {'success', 'reserved', 'denied'}:
        raise ValueError('Unsupported audit event')
    if resource_type not in {None, 'workflow', 'evidence', 'task', 'plan', 'profile', 'job', 'skill_gap'}:
        raise ValueError('Unsupported resource type')
    # Resource identifiers must be UUIDs, never CV object paths or URLs.
    resource_id = str(UUID(str(resource_id))) if resource_id is not None else None
    safe_metadata = {key: value for key, value in (metadata or {}).items()
                     if key == 'http_status' and type(value) is int and 100 <= value <= 599}
    cursor.execute('''
        INSERT INTO access_logs (user_id, action, resource_type, resource_id, outcome, metadata, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, clock_timestamp())
    ''', (user_id, action, resource_type, resource_id, outcome, Jsonb(safe_metadata)))


def log_access_event(user_id, action, resource_type=None, resource_id=None,
                     outcome='success', metadata=None):
    # Audit outages must not turn an already accepted business action into a retry.
    try:
        with pool.connection() as conn:
            with conn.cursor() as cursor:
                insert_access_event(cursor, user_id, action, resource_type, resource_id, outcome, metadata)
            conn.commit()
    except Exception:
        logger.error('Audit event persistence unavailable.')
