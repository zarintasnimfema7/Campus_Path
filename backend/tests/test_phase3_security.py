import importlib
import os
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


class Phase3SecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch('dotenv.load_dotenv'), patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CLERK_SECRET_KEY': 'test-only', 'GEMINI_API_KEY': 'test-only',
        }), patch('psycopg_pool.ConnectionPool'):
            cls.persistence = importlib.import_module('app.routes.persistence')
            cls.service = importlib.import_module('app.services.persistence')
            cls.ownership = importlib.import_module('app.services.ownership')
            cls.audit = importlib.import_module('app.services.access_logs')
            cls.rate = importlib.import_module('app.services.workflow_rate_limit')
            cls.workflow = importlib.import_module('app.routes.workflow')

    def test_all_private_routes_require_clerk(self):
        with patch('dotenv.load_dotenv'), patch.dict(os.environ, {'GEMINI_API_KEY': 'test-only'}):
            for module in ['cv', 'jobs', 'planner', 'skill_gap', 'evidence', 'replanner', 'persistence', 'workflow']:
                router = importlib.import_module('app.routes.' + module).router
                for route in router.routes:
                    self.assertIn(self.workflow.get_current_user, [d.call for d in route.dependant.dependencies], route.path)

    def test_unauthenticated_persistence_rejected(self):
        app = FastAPI()
        app.include_router(self.persistence.router)
        def reject():
            raise HTTPException(401, 'Authentication required')
        app.dependency_overrides[self.persistence.get_current_user] = reject
        with TestClient(app) as client:
            for path in ['users', 'jobs', 'profiles', 'skill-gaps', 'plans', 'evidence']:
                self.assertEqual(client.post('/data/' + path, json={}).status_code, 401)

    def test_forged_user_id_is_ignored(self):
        app = FastAPI()
        app.include_router(self.persistence.router)
        app.dependency_overrides[self.persistence.get_current_user] = lambda: {'id': 'user_A'}
        with TestClient(app) as client, patch.object(self.persistence, 'save_student_profile', return_value={}) as save, patch.object(self.persistence, 'log_access_event') as audit:
            response = client.post('/data/profiles', json={'user_id': 'user_B', 'profile': {}})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(save.call_args.args[0], 'user_A')
            audit.assert_called_once_with('user_A', 'profile_updated', 'profile')

    def test_create_user_uses_clerk_id_not_email_for_identity(self):
        app = FastAPI()
        app.include_router(self.persistence.router)
        app.dependency_overrides[self.persistence.get_current_user] = lambda: {'id': 'user_A'}
        with TestClient(app) as client, patch.object(self.persistence, 'create_user', return_value={}) as save, patch.object(self.persistence, 'log_access_event'):
            self.assertEqual(client.post('/data/users', json={'name': 'Name', 'email': 'other@example.test'}).status_code, 200)
            self.assertEqual(save.call_args.args[:3], ('user_A', 'Name', None))

    def test_owner_and_missing_queries_share_404(self):
        resource = '12345678-1234-1234-1234-123456789abc'
        for fn in [self.ownership.require_job_owner, self.ownership.require_task_owner]:
            cursor = Mock()
            cursor.fetchone.return_value = (resource,)
            fn(cursor, resource, 'user_A')
            self.assertEqual(cursor.execute.call_args.args[1], (resource, 'user_A'))
            self.assertIn('user_id = %s', cursor.execute.call_args.args[0])
            cursor.fetchone.return_value = None
            for user in ['user_A', 'user_B']:
                with self.assertRaises(HTTPException) as error:
                    fn(cursor, resource, user)
                self.assertEqual((error.exception.status_code, error.exception.detail), (404, 'Resource not found.'))

    def test_wrong_owner_evidence_never_writes(self):
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = None
        verification = Mock(overall_status='verified')
        with patch.object(self.service, 'pool') as pool:
            pool.connection.return_value.__enter__.return_value = conn
            with self.assertRaises(HTTPException):
                self.service.save_evidence('12345678-1234-1234-1234-123456789abc', verification, user_id='user_A')
        self.assertEqual(cursor.execute.call_count, 1)
        self.assertIn('JOIN plans', cursor.execute.call_args.args[0])
        conn.commit.assert_not_called()

    def test_wrong_owner_job_prevents_plan_write(self):
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value.fetchone.return_value = None
        with patch.object(self.service, 'pool') as pool:
            pool.connection.return_value.__enter__.return_value = conn
            with self.assertRaises(HTTPException):
                self.service.save_learning_plan('user_A', '12345678-1234-1234-1234-123456789abc', Mock(), 50)
        self.assertEqual(conn.cursor.return_value.__enter__.return_value.execute.call_count, 1)

    def test_audit_parameterization_and_privacy(self):
        cursor = Mock()
        self.audit.insert_access_event(cursor, 'user_A', 'profile_updated', metadata={
            'cv': 'private', 'token': 'secret', 'DATABASE_URL': 'private', 'http_status': 200,
        })
        query, values = cursor.execute.call_args.args
        self.assertNotIn('user_A', query)
        self.assertEqual(values[-1].obj, {'http_status': 200})
        self.assertIn('VALUES (%s', query)
        with self.assertRaises(ValueError):
            self.audit.insert_access_event(cursor, 'user_A', 'profile_updated', resource_id='cv/private/path')

    def test_audit_failure_does_not_expose_exception(self):
        with patch.object(self.audit, 'pool') as pool, self.assertLogs(self.audit.logger, level='ERROR') as logs:
            pool.connection.side_effect = RuntimeError('secret credential')
            self.audit.log_access_event('user_A', 'profile_updated')
        self.assertNotIn('secret credential', str(logs.output))

    def test_rate_limited_rejects_before_external_work(self):
        app = FastAPI()
        app.include_router(self.workflow.router)
        app.dependency_overrides[self.workflow.get_current_user] = lambda: {'id': 'user_A'}
        with TestClient(app) as client, patch.object(self.workflow, 'reserve_workflow_start', return_value=False), patch.object(self.workflow, 'upload_cv') as upload, patch.object(self.workflow, 'create_workflow_job') as create, patch.object(self.workflow, 'publish_workflow_job') as publish:
            response = client.post('/workflow/start', data={'job_description': 'JD'}, files={'cv': ('cv.pdf', b'cv', 'application/pdf')})
        self.assertEqual(response.status_code, 429)
        upload.assert_not_called(); create.assert_not_called(); publish.assert_not_called()

    def test_configuration_rejects_invalid_values(self):
        for value in ['0', '-1', 'bad']:
            with patch.dict(os.environ, {'WORKFLOW_START_RATE_LIMIT': value}), self.assertRaises(ValueError):
                self.rate.reserve_workflow_start('user_A')

    def test_rate_database_failure_fails_closed(self):
        with patch.object(self.workflow, 'reserve_workflow_start', side_effect=RuntimeError('private connection details')), patch.object(self.workflow, 'upload_cv') as upload:
            with self.assertRaises(HTTPException) as error:
                self.workflow.start_workflow('JD', Mock(), None, {'id': 'user_A'})
        self.assertEqual(error.exception.status_code, 503)
        self.assertNotIn('private', error.exception.detail)
        upload.assert_not_called()

    def test_foreign_task_verification_stops_before_ai(self):
        route = importlib.import_module('app.routes.evidence')
        app = FastAPI()
        app.include_router(route.router)
        app.dependency_overrides[route.get_current_user] = lambda: {'id': 'user_A'}
        payload = {'repository_url': 'https://github.com/example/repo',
                   'task_id': '12345678-1234-1234-1234-123456789abc',
                   'task': {'title': 'Task', 'target_skill': 'Skill', 'goal': 'Goal', 'action': 'Action'}}
        with TestClient(app) as client, patch.object(route, 'get_task_for_user', side_effect=HTTPException(404, 'Resource not found.')) as lookup, patch.object(route, 'verify_repository_evidence', new_callable=AsyncMock) as verify:
            response = client.post('/evidence/verify-github', json=payload)
        self.assertEqual(response.status_code, 404)
        lookup.assert_called_once_with(payload['task_id'], 'user_A')
        verify.assert_not_called()

    def test_owned_evidence_writes_in_same_transaction(self):
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value
        task_id = '12345678-1234-1234-1234-123456789abc'
        cursor.fetchone.side_effect = [{'id': task_id}, {'id': task_id}]
        verification = Mock(overall_status='verified', repository_url='https://github.com/example/repo',
                            verification_score=100, checks=[], summary='Summary')
        with patch.object(self.service, 'pool') as pool:
            pool.connection.return_value.__enter__.return_value = conn
            self.service.save_evidence(task_id, verification, user_id='user_A')
        statements = [call.args for call in cursor.execute.call_args_list]
        self.assertIn('FOR UPDATE', statements[0][0])
        self.assertIn('INSERT INTO evidence', statements[1][0])
        self.assertEqual(statements[2][1], ('verified', task_id, 'user_A'))
        conn.commit.assert_called_once()

    def test_same_user_concurrent_admission_and_independent_users(self):
        # Simulate PostgreSQL's transaction lock and committed rows, not a production limiter.
        locks, rows = {}, []
        lock_map = threading.Lock()
        class Connection:
            def __init__(self): self.lock = None; self.row = None; self.answer = None
            @contextmanager
            def cursor(self): yield self
            def execute(self, query, params=None):
                if 'pg_advisory_xact_lock' in query:
                    with lock_map: self.lock = locks.setdefault(params[0], threading.Lock())
                    self.lock.acquire()
                elif 'SELECT count' in query:
                    self.answer = (sum(r[0] == params[0] and r[1] == 'workflow_start_reserved' for r in rows),)
                    assert params[1] == 120
                elif 'INSERT INTO access_logs' in query: self.row = params
            def fetchone(self): return self.answer
            def commit(self): rows.append(self.row)
        class Pool:
            @contextmanager
            def connection(self):
                conn = Connection()
                try: yield conn
                finally:
                    if conn.lock: conn.lock.release()
        with patch.object(self.rate, 'pool', Pool()), patch.dict(os.environ, {'WORKFLOW_START_RATE_LIMIT': '3', 'WORKFLOW_START_RATE_WINDOW_SECONDS': '120'}):
            with ThreadPoolExecutor(max_workers=8) as executor:
                results = list(executor.map(lambda _: self.rate.reserve_workflow_start('user_A'), range(12)))
            self.assertEqual(sum(results), 3)
            self.assertTrue(self.rate.reserve_workflow_start('user_B'))
        self.assertEqual(sum(row[1] == 'workflow_start_rate_limited' for row in rows), 9)

    def test_polling_route_does_not_emit_audit_events(self):
        import inspect
        self.assertNotIn('log_access_event', inspect.getsource(self.workflow.get_workflow_status))


if __name__ == '__main__':
    unittest.main()
