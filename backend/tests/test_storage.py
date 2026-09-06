import io
import os
import unittest
from unittest.mock import patch

from fastapi import UploadFile
from google.api_core.exceptions import Forbidden, NotFound
from starlette.datastructures import Headers

from app.services import storage


class StorageTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(storage, '_bucket')
        self.bucket = patcher.start().return_value
        self.addCleanup(patcher.stop)

    def upload(self, filename='resume.pdf', content_type='application/pdf', data=b'cv', size=None):
        return UploadFile(
            io.BytesIO(data), filename=filename, size=size,
            headers=Headers({'content-type': content_type}),
        )

    def test_supported_formats(self):
        for extension, mime in storage._CONTENT_TYPES.items():
            with self.subTest(extension=extension):
                path = storage.upload_cv(self.upload('resume' + extension, mime), 'user_123', 'job_1')
                self.assertEqual(path, 'cv/user_123/job_1/resume' + extension)
                self.bucket.blob.return_value.upload_from_string.assert_called_with(
                    b'cv', content_type=mime, if_generation_match=0, retry=None,
                )

    def test_invalid_extension_and_mime(self):
        for filename, mime in [('resume.exe', 'application/pdf'), ('resume.pdf', 'text/html')]:
            with self.subTest(filename=filename, mime=mime), self.assertRaises(ValueError):
                storage.upload_cv(self.upload(filename, mime), 'user_123', 'job_1')
        self.bucket.blob.assert_not_called()

    def test_optional_or_generic_mime(self):
        for mime in ('', 'application/octet-stream'):
            with self.subTest(mime=mime):
                storage.upload_cv(self.upload(content_type=mime), 'user_123', 'job_1')

    def test_oversized_actual_or_reported_size(self):
        for upload in (
            self.upload(data=b'x' * (storage.MAX_CV_SIZE + 1), size=1),
            self.upload(size=storage.MAX_CV_SIZE + 1),
        ):
            with self.assertRaises(ValueError):
                storage.upload_cv(upload, 'user_123', 'job_1')
        self.bucket.blob.assert_not_called()

    def test_size_boundary_and_stream_position(self):
        upload = self.upload(data=b'x' * storage.MAX_CV_SIZE)
        upload.file.seek(3)
        storage.upload_cv(upload, 'user_123', 'job_1')
        self.assertEqual(upload.file.tell(), 3)
        self.assertEqual(len(self.bucket.blob.return_value.upload_from_string.call_args.args[0]), storage.MAX_CV_SIZE)

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            storage.upload_cv(self.upload(data=b''), 'user_123', 'job_1')
        self.bucket.blob.assert_not_called()

    def test_safe_paths_and_job_isolation(self):
        first = storage.upload_cv(self.upload(r'..\folder/../../my .. CV.PDF'), 'user_123', 'job_1')
        second = storage.upload_cv(self.upload(r'..\folder/../../my .. CV.PDF'), 'user_123', 'job_2')
        self.assertEqual(first, 'cv/user_123/job_1/my_CV.pdf')
        self.assertNotEqual(first, second)

    def test_invalid_segments(self):
        for user, job in [('user/other', 'job_1'), ('user_123', '..'), ('', 'job_1')]:
            with self.subTest(user=user, job=job), self.assertRaises(ValueError):
                storage.upload_cv(self.upload(), user, job)
        self.bucket.blob.assert_not_called()

    def test_download_and_delete(self):
        path = 'cv/user_123/job_1/resume.pdf'
        self.bucket.blob.return_value.download_as_bytes.return_value = b'private cv'
        self.assertEqual(storage.download_cv(path), b'private cv')
        self.bucket.blob.assert_called_with(path)
        storage.delete_cv(path)
        self.bucket.blob.return_value.delete.assert_called_once_with(retry=None)
        self.bucket.blob.return_value.delete.side_effect = NotFound('missing')
        storage.delete_cv(path)
        self.bucket.blob.return_value.delete.side_effect = Forbidden('denied')
        with self.assertRaises(Forbidden):
            storage.delete_cv(path)

    def test_untrusted_path_shapes_rejected(self):
        for path in ('gs://bucket/resume.pdf', '../resume.pdf', 'cv/user/job/../resume.pdf',
                     'cv/user/job/..pdf', 'cv/user/job/a\\b.pdf', 'cv/user/job/a%2fb.pdf'):
            for operation in (storage.download_cv, storage.delete_cv):
                with self.subTest(path=path, operation=operation), self.assertRaises(ValueError):
                    operation(path)
        self.bucket.blob.assert_not_called()


class ConfigurationTests(unittest.TestCase):
    def tearDown(self):
        storage._client.cache_clear()

    def test_missing_bucket_fails_before_client_initialization(self):
        with patch.dict(os.environ, {'GCS_BUCKET_NAME': ''}), patch.object(storage, '_client') as client:
            with self.assertRaisesRegex(RuntimeError, 'GCS_BUCKET_NAME'):
                storage.download_cv('cv/user/job/resume.pdf')
            client.assert_not_called()

    def test_client_reused_with_adc(self):
        storage._client.cache_clear()
        with patch.dict(os.environ, {'GCS_BUCKET_NAME': 'test-private', 'GOOGLE_CLOUD_PROJECT': 'test-project'}):
            with patch.object(storage.storage, 'Client') as client:
                storage.download_cv('cv/user/job/resume.pdf')
                storage.delete_cv('cv/user/job/resume.pdf')
                client.assert_called_once_with(project='test-project')
                client.return_value.bucket.assert_called_with('test-private')


if __name__ == '__main__':
    unittest.main()
