import importlib
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


class WorkflowStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch('dotenv.load_dotenv'), patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/test', 'CLERK_SECRET_KEY': 'test-only',
        }), patch('psycopg_pool.ConnectionPool'):
            cls.route = importlib.import_module('app.routes.workflow')
            cls.service = importlib.import_module('app.services.workflow_jobs')
        cls.app = FastAPI()
        cls.app.include_router(cls.route.router)

    def setUp(self):
        self.app.dependency_overrides[self.route.get_current_user] = lambda: {'id': 'user_owner'}
        self.addCleanup(self.app.dependency_overrides.clear)
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)
        patcher = patch.object(self.route, 'get_workflow_job_for_user')
        self.lookup = patcher.start()
        self.addCleanup(patcher.stop)
        self.job_id = '550e8400-e29b-41d4-a716-446655440000'
        self.path = '/workflow/' + self.job_id
        now = datetime(2026, 9, 5, tzinfo=timezone.utc)
        self.job = dict(id=self.job_id, status='queued', result=None, error=None,
                        retry_count=0, created_at=now, updated_at=now, started_at=None, completed_at=None)
        self.lookup.return_value = self.job

    def test_owner_states_and_minimal_contract(self):
        for status in ('queued', 'processing', 'completed', 'failed'):
            with self.subTest(status=status):
                self.lookup.return_value = {**self.job, 'status': status,
                    'result': {'plan': {'tasks': []}}, 'error': 'secret raw trace',
                    'cv_object_path': 'private', 'job_description': 'private', 'user_id': 'user_owner'}
                response = self.client.get(self.path)
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertEqual(set(body), {'job_id', 'status', 'retry_count', 'result', 'error',
                                            'created_at', 'updated_at', 'started_at', 'completed_at'})
                self.assertEqual(body['status'], status)
                self.assertEqual(body['result'], {'plan': {'tasks': []}} if status == 'completed' else None)
                self.assertEqual(body['error'], 'Workflow processing failed.' if status == 'failed' else None)
                self.assertNotIn('secret', response.text)
                self.assertNotIn('private', response.text)
                self.assertEqual(body['created_at'], '2026-09-05T00:00:00Z')
        self.lookup.assert_called_with(self.job_id, 'user_owner')

    def test_missing_and_wrong_owner_have_same_404(self):
        for reason in ('missing', 'wrong owner'):
            with self.subTest(reason=reason):
                self.lookup.return_value = None
                response = self.client.get(self.path)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json(), {'detail': 'Workflow job not found.'})

    def test_client_identity_cannot_override_clerk(self):
        response = self.client.get(self.path, params={'user_id': 'attacker', 'student_id': 'attacker'},
                                   headers={'user_id': 'attacker', 'student_id': 'attacker'})
        self.assertEqual(response.status_code, 200)
        self.lookup.assert_called_once_with(self.job_id, 'user_owner')

    def test_invalid_uuid(self):
        self.assertEqual(self.client.get('/workflow/not-a-uuid').status_code, 422)
        self.lookup.assert_not_called()

    def test_auth_required(self):
        def reject():
            raise HTTPException(status_code=401, detail='Unauthenticated')
        self.app.dependency_overrides[self.route.get_current_user] = reject
        self.assertEqual(self.client.get(self.path).status_code, 401)
        self.lookup.assert_not_called()

    def test_database_error_sanitized(self):
        self.lookup.side_effect = RuntimeError('secret database URL')
        with self.assertLogs(self.route.logger, level='ERROR') as logs:
            response = self.client.get(self.path)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret', response.text + str(logs.output))

    def test_read_only_endpoint_and_sql_ownership(self):
        # Exercise the real read service through HTTP with only the pool mocked.
        self.lookup.side_effect = self.service.get_workflow_job_for_user
        with patch.object(self.service, 'pool') as pool:
            conn = pool.connection.return_value.__enter__.return_value
            cursor = conn.cursor.return_value.__enter__.return_value
            cursor.fetchone.return_value = self.job
            with patch.object(self.route, 'publish_workflow_job') as publish, \
                 patch.object(self.route, 'upload_cv') as upload, \
                 patch.object(self.service, 'claim_workflow_job') as claim:
                self.assertEqual(self.client.get(self.path).status_code, 200)
                publish.assert_not_called()
                upload.assert_not_called()
                claim.assert_not_called()
            cursor.execute.assert_called_once()
            query, params = cursor.execute.call_args.args
            sql = ' '.join(query.split())
            self.assertTrue(sql.startswith('SELECT '))
            self.assertIn('WHERE id = %s AND user_id = %s', sql)
            self.assertEqual(params, (self.job_id, 'user_owner'))
            self.assertNotIn(self.job_id, query)
            for forbidden in ('UPDATE', 'INSERT', 'DELETE', 'cv_object_path', 'job_description'):
                self.assertNotIn(forbidden, query)
            conn.commit.assert_not_called()

    def test_service_no_matching_row(self):
        with patch.object(self.service, 'pool') as pool:
            cursor = pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
            cursor.fetchone.return_value = None
            for user in ('user_owner', 'wrong_user'):
                self.assertIsNone(self.service.get_workflow_job_for_user(self.job_id, user))
                self.assertEqual(cursor.execute.call_args.args[1], (self.job_id, user))


if __name__ == '__main__':
    unittest.main()
