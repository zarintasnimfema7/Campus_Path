import importlib
import os
import unittest
from unittest.mock import patch


class WorkflowRetryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch('dotenv.load_dotenv'), patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
        }), patch('psycopg_pool.ConnectionPool'):
            cls.service = importlib.import_module('app.services.workflow_jobs')

    def setUp(self):
        patcher = patch.object(self.service, 'pool')
        self.pool = patcher.start()
        self.addCleanup(patcher.stop)
        self.conn = self.pool.connection.return_value.__enter__.return_value
        self.cursor = self.conn.cursor.return_value.__enter__.return_value

    def test_atomic_sql_and_returned_attempts(self):
        for count in (1, 2, 4, 5):
            with self.subTest(count=count):
                self.cursor.execute.reset_mock()
                row = {'id': 'job', 'retry_count': count, 'status': 'failed' if count == 5 else 'queued'}
                self.cursor.fetchone.return_value = row
                self.assertEqual(self.service.record_workflow_job_failure('job', 'secret', 5), row)
                self.cursor.execute.assert_called_once()
                query, params = self.cursor.execute.call_args.args
                sql = ' '.join(query.split())
                self.assertEqual(sql.count('UPDATE'), 1)
                self.assertNotIn('SELECT', sql)
                self.assertIn("WHERE id = %s AND status = 'processing'", sql)
                self.assertIn('retry_count = retry_count + 1', sql)
                self.assertIn("status = CASE WHEN retry_count + 1 >= %s THEN 'failed' ELSE 'queued' END", sql)
                self.assertIn('completed_at = CASE WHEN retry_count + 1 >= %s THEN NOW() ELSE NULL END', sql)
                self.assertIn('started_at = CASE WHEN retry_count + 1 >= %s THEN started_at ELSE NULL END', sql)
                self.assertIn('RETURNING id, status, retry_count', sql)
                self.assertEqual(params, (5, 'Workflow processing failed.', 5, 5, 'job'))
        self.assertEqual(self.conn.commit.call_count, 4)

    def test_nonprocessing_jobs_unchanged(self):
        for state in ('queued', 'completed', 'failed', 'missing'):
            with self.subTest(state=state):
                self.cursor.fetchone.return_value = None
                self.assertIsNone(self.service.record_workflow_job_failure('job', 'safe', 5))

    def test_update_and_commit_errors_propagate(self):
        for operation in (self.cursor.execute, self.conn.commit):
            operation.side_effect = RuntimeError('DB failed')
            with self.assertRaises(RuntimeError):
                self.service.record_workflow_job_failure('job', 'safe', 5)
            operation.side_effect = None

    def test_delivery_lookup_read_only(self):
        self.cursor.fetchone.return_value = {'status': 'processing', 'retry_count': 2}
        self.assertEqual(self.service.get_workflow_job_delivery_state('job'), {'status': 'processing', 'retry_count': 2})
        self.cursor.execute.assert_called_once_with('SELECT status, retry_count FROM workflow_jobs WHERE id = %s', ('job',))
        self.conn.commit.assert_not_called()
