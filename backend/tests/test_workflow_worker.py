import base64
import importlib
import json
import os
import sys
from types import ModuleType
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


class WorkflowWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch('dotenv.load_dotenv'), patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
        }), patch('psycopg_pool.ConnectionPool'):
            cls.worker = importlib.import_module('app.services.workflow_worker')
            cls.route = importlib.import_module('app.routes.workflow_worker')
        app = FastAPI()
        app.include_router(cls.route.router)
        cls.app = app

    def setUp(self):
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)
        for name in ('claim_workflow_job', 'download_cv', 'mark_workflow_job_completed', 'record_workflow_job_failure', 'get_workflow_job_delivery_state'):
            patcher = patch.object(self.worker, name)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        self.workflow = AsyncMock(return_value={'result': 'internal only'})
        module = ModuleType('app.services.workflow')
        module.run_initial_workflow = self.workflow
        modules = patch.dict(sys.modules, {'app.services.workflow': module})
        modules.start()
        self.addCleanup(modules.stop)
        self.job_id = '550e8400-e29b-41d4-a716-446655440000'
        self.job = {
            'user_id': 'user_trusted', 'job_description': 'trusted JD',
            'target_role': 'optional role', 'cv_object_path': 'cv/user_trusted/job/resume.pdf',
        }
        self.claim_workflow_job.return_value = self.job
        self.download_cv.return_value = b'private CV'
        self.get_workflow_job_delivery_state.return_value = None
        config = patch.dict(os.environ, {'WORKFLOW_MAX_RETRIES': '5'})
        config.start()
        self.addCleanup(config.stop)

    def envelope(self, payload=None):
        return {'message': {'data': base64.b64encode(json.dumps(
            payload if payload is not None else {'job_id': self.job_id}
        ).encode()).decode(), 'messageId': 'test-message'}, 'subscription': 'test-subscription'}

    def post(self, envelope=None):
        return self.client.post('/internal/workflow-jobs/process', json=self.envelope() if envelope is None else envelope)

    def test_transport_passes_only_uuid(self):
        with patch.object(self.route, 'process_workflow_job') as process:
            response = self.post(self.envelope({
                'job_id': self.job_id, 'user_id': 'attacker', 'job_description': 'untrusted',
                'cv_object_path': 'untrusted',
            }))
            self.assertEqual(response.status_code, 204)
            self.assertEqual(response.content, b'')
            process.assert_called_once_with(self.job_id)

    def test_success_uses_only_claimed_data(self):
        response = self.post(self.envelope({
            'job_id': self.job_id, 'user_id': 'attacker', 'job_description': 'untrusted',
            'cv_object_path': 'untrusted',
        }))
        self.assertEqual(response.status_code, 204)
        self.claim_workflow_job.assert_called_once_with(self.job_id)
        self.download_cv.assert_called_once_with(self.job['cv_object_path'])
        self.workflow.assert_awaited_once_with(
            user_id='user_trusted', job_description='trusted JD',
            cv_filename='resume.pdf', cv_bytes=b'private CV',
        )
        self.mark_workflow_job_completed.assert_called_once_with(self.job_id, self.workflow.return_value)
        self.record_workflow_job_failure.assert_not_called()

    def test_internal_result_returned(self):
        self.assertEqual(self.worker.process_workflow_job(self.job_id), {'result': 'internal only'})

    def test_unclaimed_delivery_states(self):
        self.claim_workflow_job.return_value = None
        for state in ('queued', 'processing', 'failed', 'completed'):
            with self.subTest(state=state):
                self.get_workflow_job_delivery_state.return_value = {'status': state, 'retry_count': 5}
                if state == 'completed':
                    self.assertEqual(self.post().status_code, 204)
                else:
                    with self.assertLogs(self.route.logger, level='ERROR'):
                        self.assertEqual(self.post().status_code, 500)
        self.workflow.assert_not_called()
        self.record_workflow_job_failure.assert_not_called()

    def test_five_failures_and_terminal_redelivery(self):
        state = {'status': 'queued', 'retry_count': 0}
        def claim(job_id):
            if state['status'] != 'queued':
                return None
            state['status'] = 'processing'
            return self.job
        def record(job_id, error, limit):
            state['retry_count'] += 1
            state['status'] = 'failed' if state['retry_count'] >= limit else 'queued'
            return dict(state)
        self.claim_workflow_job.side_effect = claim
        self.record_workflow_job_failure.side_effect = record
        self.get_workflow_job_delivery_state.side_effect = lambda job_id: dict(state)
        self.workflow.side_effect = RuntimeError('processing failure')
        with patch('app.services.pubsub.publish_workflow_job') as publish:
            for attempt in range(1, 6):
                envelope = self.envelope()
                envelope['deliveryAttempt'] = 999  # Never substitutes for DB count.
                with self.assertLogs(self.route.logger, level='ERROR'):
                    self.assertEqual(self.post(envelope).status_code, 500)
                self.assertEqual(state['retry_count'], attempt)
                self.assertEqual(state['status'], 'failed' if attempt == 5 else 'queued')
                self.assertEqual(self.workflow.await_count, attempt)
            with self.assertLogs(self.route.logger, level='ERROR'):
                self.assertEqual(self.post().status_code, 500)
            self.assertEqual(self.workflow.await_count, 5)
            self.assertEqual(self.record_workflow_job_failure.call_count, 5)
            publish.assert_not_called()

    def test_retry_configuration(self):
        for raw, expected in [('5', 5), ('3', 3), ('0', 5), ('-1', 5), ('invalid', 5)]:
            with patch.dict(os.environ, {'WORKFLOW_MAX_RETRIES': raw}):
                self.assertEqual(self.worker.workflow_max_retries(), expected)

    def test_unclaimable_acknowledged_without_work(self):
        self.claim_workflow_job.return_value = None
        self.assertEqual(self.post().status_code, 204)
        self.download_cv.assert_not_called()
        self.workflow.assert_not_called()
        self.mark_workflow_job_completed.assert_not_called()
        self.record_workflow_job_failure.assert_not_called()

    def test_duplicate_delivery_runs_once(self):
        self.claim_workflow_job.side_effect = [self.job, None]
        self.assertEqual(self.post().status_code, 204)
        self.assertEqual(self.post().status_code, 204)
        self.download_cv.assert_called_once()
        self.workflow.assert_awaited_once()
        self.mark_workflow_job_completed.assert_called_once()

    def test_malformed_messages_rejected_before_claim(self):
        bad_envelopes = [
            {}, {'message': {}}, {'message': None}, {'message': {'data': None}},
            {'message': {'data': '%%%'}},
            {'message': {'data': base64.b64encode(b'not JSON').decode()}},
            {'message': {'data': base64.b64encode(b'\xff').decode()}},
            self.envelope({}), self.envelope({'job_id': 'bad'}),
            self.envelope({'job_id': None}), self.envelope({'job_id': 123}),
            self.envelope([]), self.envelope('invalid'),
        ]
        for envelope in bad_envelopes:
            with self.subTest(envelope=envelope):
                response = self.post(envelope)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()['detail'], 'Invalid Pub/Sub workflow message.')
        self.claim_workflow_job.assert_not_called()
        self.mark_workflow_job_completed.assert_not_called()
        self.record_workflow_job_failure.assert_not_called()
        self.download_cv.assert_not_called()
        self.workflow.assert_not_called()

    def test_missing_cv_fails_without_download(self):
        self.claim_workflow_job.return_value = {**self.job, 'cv_object_path': None}
        with self.assertLogs(self.route.logger, level='ERROR'):
            self.assertEqual(self.post().status_code, 500)
        self.download_cv.assert_not_called()
        self.workflow.assert_not_called()

    def test_processing_errors_not_acknowledged_or_exposed(self):
        for operation in (self.claim_workflow_job, self.download_cv, self.workflow):
            with self.subTest(operation=operation):
                operation.side_effect = RuntimeError('secret CV credentials')
                with self.assertLogs(self.route.logger, level='ERROR') as logs:
                    response = self.post()
                self.assertEqual(response.status_code, 500)
                self.assertEqual(response.json()['detail'], 'Workflow processing failed.')
                self.assertNotIn('secret', response.text + str(logs.output))
                operation.side_effect = None

    def test_processing_failure_records_safe_error(self):
        for operation in (self.download_cv, self.workflow):
            with self.subTest(operation=operation):
                self.record_workflow_job_failure.reset_mock()
                operation.side_effect = RuntimeError('secret CV credentials')
                with self.assertLogs(self.route.logger, level='ERROR'):
                    self.assertEqual(self.post().status_code, 500)
                self.record_workflow_job_failure.assert_called_once_with(self.job_id, 'Workflow processing failed.', 5)
                self.mark_workflow_job_completed.assert_not_called()
                operation.side_effect = None

    def test_failed_update_preserves_original_error(self):
        original = RuntimeError('original processing failure')
        self.workflow.side_effect = original
        for outcome in (False, RuntimeError('secret DB credentials')):
            self.record_workflow_job_failure.side_effect = outcome if isinstance(outcome, Exception) else None
            self.record_workflow_job_failure.return_value = False
            with self.assertLogs(self.worker.logger, level='ERROR') as logs:
                with self.assertRaises(RuntimeError) as caught:
                    self.worker.process_workflow_job(self.job_id)
            self.assertIs(caught.exception, original)
            self.assertNotIn('secret', str(logs.output))

    def test_completion_update_failure_returns_500_without_retry(self):
        for outcome in (False, RuntimeError('secret DB credentials')):
            self.workflow.reset_mock()
            self.mark_workflow_job_completed.side_effect = outcome if isinstance(outcome, Exception) else None
            self.mark_workflow_job_completed.return_value = False
            with self.assertLogs(self.route.logger, level='ERROR'):
                self.assertEqual(self.post().status_code, 500)
            self.workflow.assert_awaited_once()
            self.record_workflow_job_failure.assert_not_called()


if __name__ == '__main__':
    unittest.main()
