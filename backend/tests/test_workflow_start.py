import importlib
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


class WorkflowStartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Import the real route without opening Neon or loading local credentials.
        with patch('dotenv.load_dotenv'), patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CLERK_SECRET_KEY': 'test-only',
        }), patch('psycopg_pool.ConnectionPool'):
            cls.route = importlib.import_module('app.routes.workflow')
        cls.app = FastAPI()
        cls.app.include_router(cls.route.router)

    def setUp(self):
        self.app.dependency_overrides[self.route.get_current_user] = lambda: {'id': 'user_verified'}
        self.addCleanup(self.app.dependency_overrides.clear)
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)
        for name in ('upload_cv', 'ensure_user_exists', 'create_workflow_job', 'delete_cv', 'publish_workflow_job', 'delete_workflow_job', 'reserve_workflow_start', 'log_access_event'):
            patcher = patch.object(self.route, name)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        self.upload_cv.side_effect = lambda **kw: f"cv/{kw['user_id']}/{kw['job_id']}/resume.pdf"

    def post(self, data=None, filename='resume.pdf', content=b'cv', mime='application/pdf'):
        return self.client.post(
            '/workflow/start', data=data or {'job_description': '  Backend developer  '},
            files={'cv': (filename, content, mime)},
        )

    def test_accepted_uuid_and_clerk_identity(self):
        response = self.post({'job_description': '  Backend developer  ', 'user_id': 'attacker', 'student_id': 'attacker'})
        self.assertEqual(response.status_code, 202)
        body = response.json()
        self.assertEqual(set(body), {'job_id', 'status'})
        self.assertEqual(UUID(body['job_id']).version, 4)
        self.assertEqual(body['status'], 'queued')
        self.assertEqual(self.upload_cv.call_args.kwargs['user_id'], 'user_verified')
        self.assertEqual(self.upload_cv.call_args.kwargs['job_id'], body['job_id'])
        self.ensure_user_exists.assert_called_once_with(user_id='user_verified', email=None, name=None)
        self.create_workflow_job.assert_called_once_with(
            job_id=body['job_id'], user_id='user_verified', job_description='Backend developer',
            target_role=None, cv_object_path=f"cv/user_verified/{body['job_id']}/resume.pdf",
        )
        self.delete_cv.assert_not_called()
        self.publish_workflow_job.assert_called_once_with(job_id=body['job_id'], ordering_key='user_verified')
        self.delete_workflow_job.assert_not_called()

    def test_target_role(self):
        for supplied, expected in [('  Engineer  ', 'Engineer'), ('  ', None)]:
            with self.subTest(role=supplied):
                response = self.post({'job_description': 'JD', 'target_role': supplied})
                self.assertEqual(response.status_code, 202)
                self.assertEqual(self.create_workflow_job.call_args.kwargs['target_role'], expected)

    def test_ordering_identity_cannot_be_overridden(self):
        response = self.client.post(
            '/workflow/start?ordering_key=attacker&user_id=attacker',
            data={'job_description': 'JD', 'ordering_key': 'attacker', 'user_id': 'attacker'},
            headers={'ordering_key': 'attacker', 'user_id': 'attacker'},
            files={'cv': ('resume.pdf', b'cv', 'application/pdf')},
        )
        self.assertEqual(response.status_code, 202)
        self.publish_workflow_job.assert_called_once_with(
            job_id=response.json()['job_id'], ordering_key='user_verified',
        )

    def test_real_storage_validation(self):
        from app.services import storage
        self.upload_cv.side_effect = storage.upload_cv
        with patch.object(storage, '_bucket') as bucket:
            for filename, content, mime in [
                ('resume.exe', b'cv', 'application/pdf'),
                ('resume.pdf', b'', 'application/pdf'),
                ('resume.pdf', b'x' * (storage.MAX_CV_SIZE + 1), 'application/pdf'),
                ('resume.pdf', b'cv', 'text/html'),
            ]:
                with self.subTest(filename=filename, size=len(content), mime=mime):
                    self.assertEqual(self.post(filename=filename, content=content, mime=mime).status_code, 400)
            bucket.assert_not_called()
        self.create_workflow_job.assert_not_called()
        self.ensure_user_exists.assert_not_called()

    def test_blank_description(self):
        self.assertEqual(self.post({'job_description': '  '}).status_code, 400)
        self.upload_cv.assert_not_called()

    def test_upload_failure(self):
        self.upload_cv.side_effect = RuntimeError('secret storage credentials')
        with self.assertLogs(self.route.logger, level='ERROR') as logs:
            response = self.post()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret', response.text + str(logs.output))
        self.create_workflow_job.assert_not_called()
        self.delete_cv.assert_not_called()

    def test_database_failure_cleanup_and_original_cause(self):
        for cleanup_fails in (False, True):
            with self.subTest(cleanup_fails=cleanup_fails):
                self.create_workflow_job.side_effect = RuntimeError('secret database credentials')
                self.delete_cv.side_effect = RuntimeError('secret cleanup credentials') if cleanup_fails else None
                with self.assertLogs(self.route.logger, level='ERROR') as logs:
                    response = self.post()
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()['detail'], 'Could not create workflow job. Please try again.')
                self.delete_cv.assert_called_with(self.create_workflow_job.call_args.kwargs['cv_object_path'])
                self.assertNotIn('secret', response.text + str(logs.output))

    def test_user_creation_failure_also_cleans_up(self):
        self.ensure_user_exists.side_effect = RuntimeError('database unavailable')
        with self.assertLogs(self.route.logger, level='ERROR'):
            self.assertEqual(self.post().status_code, 503)
        self.delete_cv.assert_called_once()
        self.create_workflow_job.assert_not_called()

    def test_authentication_required(self):
        def reject():
            raise HTTPException(status_code=401, detail='Unauthenticated')
        self.app.dependency_overrides[self.route.get_current_user] = reject
        self.assertEqual(self.post().status_code, 401)
        self.upload_cv.assert_not_called()
        self.create_workflow_job.assert_not_called()

    def test_route_has_no_ai_execution(self):
        source = Path(self.route.__file__).read_text()
        self.assertNotIn('run_initial_workflow', source)
        workflow_source = Path(self.route.__file__).parents[1] / 'services' / 'workflow.py'
        self.assertIn('async def run_initial_workflow(', workflow_source.read_text())

    def test_publish_runs_after_insert(self):
        def publish(job_id, ordering_key):
            self.create_workflow_job.assert_called_once()
            self.assertEqual(self.create_workflow_job.call_args.kwargs['job_id'], job_id)
            return 'internal-message-id'
        self.publish_workflow_job.side_effect = publish
        response = self.post()
        self.assertEqual(response.status_code, 202)
        self.assertNotIn('internal-message-id', response.text)

    def test_publish_failure_compensation(self):
        for row_fails, cv_fails in ((False, False), (True, False), (False, True), (True, True)):
            with self.subTest(row_fails=row_fails, cv_fails=cv_fails):
                self.delete_workflow_job.reset_mock()
                self.delete_cv.reset_mock()
                self.publish_workflow_job.side_effect = RuntimeError('secret publish credentials')
                self.delete_workflow_job.side_effect = ValueError('secret DB') if row_fails else None
                self.delete_cv.side_effect = ValueError('secret GCS') if cv_fails else None
                with self.assertLogs(self.route.logger, level='ERROR') as logs:
                    response = self.post()
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()['detail'], 'Could not publish workflow job. Please try again.')
                job = self.create_workflow_job.call_args.kwargs
                self.delete_workflow_job.assert_called_once_with(job['job_id'], 'user_verified')
                self.delete_cv.assert_called_once_with(job['cv_object_path'])
                self.assertNotIn('secret', response.text + str(logs.output))
                self.assertIn('Workflow publish failed', logs.output[0])

    def test_original_publish_exception_preserved(self):
        error = RuntimeError('publish failed')
        self.publish_workflow_job.side_effect = error
        self.delete_workflow_job.side_effect = ValueError('cleanup failed')
        self.delete_cv.side_effect = ValueError('cleanup failed')
        with self.assertLogs(self.route.logger, level='ERROR'), self.assertRaises(HTTPException) as caught:
            self.route.start_workflow(job_description='JD', cv=Mock(), target_role=None, current_user={'id': 'user_verified'})
        self.assertIs(caught.exception.__cause__, error)

    def test_no_publish_after_database_failure(self):
        self.create_workflow_job.side_effect = RuntimeError('DB failed')
        with self.assertLogs(self.route.logger, level='ERROR'):
            self.assertEqual(self.post().status_code, 503)
        self.publish_workflow_job.assert_not_called()

    def test_parameterized_database_delete(self):
        service = importlib.import_module('app.services.workflow_jobs')
        with patch.object(service, 'pool') as pool:
            conn = pool.connection.return_value.__enter__.return_value
            cursor = conn.cursor.return_value.__enter__.return_value
            service.delete_workflow_job('job', 'user')
            cursor.execute.assert_called_once_with(
                'DELETE FROM workflow_jobs WHERE id = %s AND user_id = %s', ('job', 'user'),
            )
            conn.commit.assert_called_once()

    def test_parameterized_database_insert(self):
        service = importlib.import_module('app.services.workflow_jobs')
        with patch.object(service, 'pool') as pool:
            conn = pool.connection.return_value.__enter__.return_value
            cursor = conn.cursor.return_value.__enter__.return_value
            args = ('550e8400-e29b-41d4-a716-446655440000', 'user_verified', "JD'; DROP TABLE users;--", None, 'cv/user/job/resume.pdf')
            service.create_workflow_job(*args)
            query, params = cursor.execute.call_args.args
            self.assertEqual(params, args)
            self.assertNotIn(args[2], query)
            self.assertIn("'queued'", query)
            conn.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
