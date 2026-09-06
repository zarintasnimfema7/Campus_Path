import importlib
import json
import os
import unittest
from unittest.mock import patch

from psycopg.types.json import Jsonb
from app.models.workflow import WorkflowResult


class WorkflowStateTests(unittest.TestCase):
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
        self.cursor.fetchone.return_value = ('job', 'completed')

    def test_completed_jsonb_and_guard(self):
        result = WorkflowResult(
            user_id='user_test', job_target_id='target', profile_id='profile', plan_id='plan',
            job={'job_title': 'Engineer', 'required_skills': ['Python']},
            student={'name': 'Test', 'skills': ['Python']},
            skill_gap={'readiness_score': 80, 'required_score': 80, 'preferred_score': 80},
            plan={'plan_title': 'Learning plan', 'summary': 'Practice', 'tasks': [
                {'title': 'Build', 'target_skill': 'Python', 'goal': 'Learn', 'action': 'Practice'},
            ]},
        )
        self.assertTrue(self.service.mark_workflow_job_completed('job', result))
        self.cursor.execute.assert_called_once()
        query, params = self.cursor.execute.call_args.args
        sql = ' '.join(query.split())
        self.assertIn("WHERE id = %s AND status = 'processing'", sql)
        self.assertIn("status = 'completed', result = %s, error = NULL", sql)
        self.assertIn('completed_at = NOW(), updated_at = NOW()', sql)
        self.assertIn('RETURNING id, status', sql)
        self.assertIsInstance(params[0], Jsonb)
        self.assertEqual(json.loads(json.dumps(params[0].obj)), result.model_dump(mode='json'))
        self.assertEqual(params[1], 'job')
        self.conn.commit.assert_called_once_with()

    def test_failed_safe_error_and_guard(self):
        self.assertTrue(self.service.mark_workflow_job_failed('job', 'secret database URL'))
        query, params = self.cursor.execute.call_args.args
        sql = ' '.join(query.split())
        self.assertIn("status = 'failed', error = %s", sql)
        self.assertIn("WHERE id = %s AND status = 'processing'", sql)
        self.assertIn('updated_at = NOW(), completed_at = NOW()', sql)
        self.assertIn('RETURNING id, status', sql)
        self.assertNotIn('retry_count', sql)
        self.assertEqual(params, ('Workflow processing failed.', 'job'))
        self.assertNotIn('secret', query)
        self.conn.commit.assert_called_once_with()

    def test_nonprocessing_states_cannot_be_overwritten(self):
        for state in ('queued', 'completed', 'failed', 'missing'):
            for function, value in ((self.service.mark_workflow_job_completed, {}),
                                    (self.service.mark_workflow_job_failed, 'failure')):
                with self.subTest(state=state, function=function):
                    self.cursor.fetchone.return_value = None
                    self.assertFalse(function('job', value))
                    query = self.cursor.execute.call_args.args[0]
                    self.assertIn("AND status = 'processing'", query)

    def test_database_failures_propagate(self):
        for function, value in ((self.service.mark_workflow_job_completed, {}),
                                (self.service.mark_workflow_job_failed, 'failure')):
            for operation in (self.cursor.execute, self.conn.commit):
                with self.subTest(function=function, operation=operation):
                    operation.side_effect = RuntimeError('DB failed')
                    with self.assertRaises(RuntimeError):
                        function('job', value)
                    operation.side_effect = None


if __name__ == '__main__':
    unittest.main()
