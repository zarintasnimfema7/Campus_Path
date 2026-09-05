import importlib
import os
import unittest
from unittest.mock import patch

from psycopg.rows import dict_row


class WorkflowClaimTests(unittest.TestCase):
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
        self.context = self.pool.connection.return_value
        self.conn = self.context.__enter__.return_value
        self.cursor_context = self.conn.cursor.return_value
        self.cursor = self.cursor_context.__enter__.return_value
        self.job_id = '550e8400-e29b-41d4-a716-446655440000'
        self.job = {
            'id': self.job_id, 'user_id': 'user_trusted', 'target_role': None,
            'job_description': 'JD', 'cv_object_path': 'cv/user/job/resume.pdf',
            'status': 'processing', 'retry_count': 0, 'created_at': 'created',
            'updated_at': 'now', 'started_at': 'now', 'completed_at': None,
        }

    def test_one_parameterized_update_returns_claimed_data(self):
        self.cursor.fetchone.return_value = self.job
        self.assertEqual(self.service.claim_workflow_job(self.job_id), self.job)
        self.cursor.execute.assert_called_once()
        query, params = self.cursor.execute.call_args.args
        sql = ' '.join(query.split())
        self.assertEqual(params, (self.job_id,))
        self.assertNotIn(self.job_id, query)
        self.assertEqual(sql.count('UPDATE'), 1)
        self.assertNotIn('SELECT', sql.upper())
        self.assertIn("WHERE id = %s AND status = 'queued'", sql)
        self.assertIn("SET status = 'processing', started_at = NOW(), updated_at = NOW()", sql)
        self.assertEqual(
            [field.strip() for field in sql.split('RETURNING ')[1].split(',')],
            list(self.job),
        )
        self.conn.cursor.assert_called_once_with(row_factory=dict_row)
        self.conn.commit.assert_called_once_with()

    def test_unavailable_jobs_return_none(self):
        # These states all yield no RETURNING row under the queued predicate.
        for state in ('processing', 'completed', 'failed', 'missing'):
            with self.subTest(state=state):
                self.cursor.fetchone.return_value = None
                self.assertIsNone(self.service.claim_workflow_job(self.job_id))

    def test_two_attempts_only_first_receives_ownership(self):
        self.cursor.fetchone.side_effect = [self.job, None]
        self.assertEqual(self.service.claim_workflow_job(self.job_id), self.job)
        self.assertIsNone(self.service.claim_workflow_job(self.job_id))
        self.assertEqual(self.conn.commit.call_count, 2)

    def test_commit_and_release_before_return(self):
        events = []
        self.cursor.fetchone.return_value = self.job
        self.cursor_context.__exit__.side_effect = lambda *args: events.append('cursor closed')
        self.conn.commit.side_effect = lambda: events.append('committed')
        self.context.__exit__.side_effect = lambda *args: events.append('connection released')
        self.service.claim_workflow_job(self.job_id)
        events.append('returned')
        self.assertEqual(events, ['cursor closed', 'committed', 'connection released', 'returned'])

    def test_database_failures_never_return_claim(self):
        for operation in (self.cursor.execute, self.conn.commit):
            with self.subTest(operation=operation):
                self.conn.commit.reset_mock()
                self.context.__exit__.reset_mock()
                self.cursor.fetchone.return_value = self.job
                operation.side_effect = RuntimeError('secret connection details')
                with self.assertRaisesRegex(RuntimeError, '^Could not claim workflow job.$') as caught:
                    self.service.claim_workflow_job(self.job_id)
                self.assertTrue(caught.exception.__suppress_context__)
                self.context.__exit__.assert_called_once()
                self.assertIs(self.context.__exit__.call_args.args[0], RuntimeError)
                if operation is self.cursor.execute:
                    self.conn.commit.assert_not_called()
                operation.side_effect = None


if __name__ == '__main__':
    unittest.main()
