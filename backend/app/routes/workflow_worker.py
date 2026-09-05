"""Internal Pub/Sub push transport.

Google service-to-service authentication must be enforced during deployment.
No Clerk dependency: this endpoint is not intended for end-user access.
Do not enable live push delivery before job finalization is implemented.
"""

import base64
import binascii
import json
import logging
from uuid import UUID

from fastapi import APIRouter, Body, HTTPException, Response

from app.services.workflow_worker import process_workflow_job


logger = logging.getLogger(__name__)
router = APIRouter(prefix='/internal/workflow-jobs', tags=['Internal workflow worker'])


def _job_id_from_envelope(envelope: dict) -> str:
    try:
        data = envelope['message']['data']
        if not isinstance(data, str):
            raise ValueError('Invalid data type')
        payload = json.loads(base64.b64decode(data, validate=True).decode('utf-8'))
        # All other message fields are ignored; identity and inputs come from DB.
        job_id = payload['job_id']
        if not isinstance(job_id, str):
            raise ValueError('Invalid job ID type')
        return str(UUID(job_id))
    except (KeyError, TypeError, ValueError, binascii.Error):
        raise HTTPException(status_code=400, detail='Invalid Pub/Sub workflow message.') from None


@router.post('/process', status_code=204, response_class=Response)
def process_message(envelope: dict = Body(...)):
    # FastAPI runs this sync handler in a thread pool, including the AI workflow.
    job_id = _job_id_from_envelope(envelope)
    try:
        process_workflow_job(job_id)
    except Exception as error:
        logger.error('Workflow processing failed for job %s (%s).', job_id, type(error).__name__)
        raise HTTPException(status_code=500, detail='Workflow processing failed.') from None
    return Response(status_code=204)
