"""Private CV storage using Application Default Credentials.

These synchronous functions are backend-internal. Async callers should run them
in a thread pool. Download/delete paths must come from a trusted job record after
the caller checks ownership; path validation alone does not authorize access.
The configured bucket must be private; this module never changes bucket IAM/ACLs.
"""

from functools import lru_cache
import os
import re

from fastapi import UploadFile
from google.api_core.exceptions import NotFound
from google.cloud import storage


# Match the existing CV endpoints' 5 MiB limit.
MAX_CV_SIZE = 5 * 1024 * 1024
_CONTENT_TYPES = {
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}
_SEGMENT = re.compile(r'[A-Za-z0-9_-]{1,128}')


def _safe_filename(filename: str) -> str:
    # Strip client directory components on either OS before sanitizing the name.
    basename = filename.replace('\\', '/').rsplit('/', 1)[-1]
    stem, extension = os.path.splitext(basename)
    extension = extension.lower()
    if extension not in _CONTENT_TYPES:
        raise ValueError('Only PDF, DOC, and DOCX CV files are supported.')
    stem = re.sub(r'[^A-Za-z0-9_-]+', '_', stem).strip('_-')[:100]
    return (stem or 'cv') + extension


def _object_path(filename: str, user_id: str, job_id: str) -> str:
    if not _SEGMENT.fullmatch(user_id) or not _SEGMENT.fullmatch(job_id):
        raise ValueError('user_id and job_id must be safe nonempty path segments.')
    return f'cv/{user_id}/{job_id}/{_safe_filename(filename)}'


def _validate_object_path(object_path: str) -> None:
    parts = object_path.split('/')
    if len(parts) != 4 or parts[0] != 'cv':
        raise ValueError('Invalid CV object path.')
    if _object_path(parts[3], parts[1], parts[2]) != object_path:
        raise ValueError('Invalid CV object path.')


@lru_cache(maxsize=1)
def _client(project: str | None) -> storage.Client:
    # ADC locally; the attached service account on Cloud Run. No key file needed.
    return storage.Client(project=project)


def _bucket():
    name = os.environ.get('GCS_BUCKET_NAME', '').strip()
    if not name:
        raise RuntimeError('GCS_BUCKET_NAME must be configured to use CV storage.')
    project = os.environ.get('GOOGLE_CLOUD_PROJECT', '').strip() or None
    return _client(project).bucket(name)


def upload_cv(file: UploadFile, user_id: str, job_id: str) -> str:
    """Validate and upload an UploadFile; return its private object path only."""
    object_path = _object_path(file.filename or '', user_id, job_id)
    extension = os.path.splitext(object_path)[1]
    expected_type = _CONTENT_TYPES[extension]
    content_type = (file.content_type or '').split(';', 1)[0].strip().lower()
    if content_type not in ('', 'application/octet-stream', expected_type):
        raise ValueError('CV content type does not match its filename extension.')
    if file.size is not None and file.size > MAX_CV_SIZE:
        raise ValueError('CV must be 5 MiB or smaller.')

    # Bound memory use and verify actual bytes, even if reported size is wrong.
    position = file.file.tell()
    try:
        file.file.seek(0)
        contents = file.file.read(MAX_CV_SIZE + 1)
    finally:
        file.file.seek(position)
    if len(contents) > MAX_CV_SIZE:
        raise ValueError('CV must be 5 MiB or smaller.')
    if not contents:
        raise ValueError('Uploaded CV is empty.')

    _bucket().blob(object_path).upload_from_string(
        contents, content_type=expected_type, if_generation_match=0, retry=None,
    )
    return object_path


def download_cv(object_path: str) -> bytes:
    """Read a CV using a trusted, ownership-checked job's stored object path."""
    _validate_object_path(object_path)
    return _bucket().blob(object_path).download_as_bytes(retry=None)


def delete_cv(object_path: str) -> None:
    """Delete a trusted job's CV; an already absent object is a successful no-op."""
    _validate_object_path(object_path)
    try:
        _bucket().blob(object_path).delete(retry=None)
    except NotFound:
        pass
