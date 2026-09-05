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
        for name in ('claim_workflow_job', 'download_cv'):
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

    def test_internal_result_returned(self):
        self.assertEqual(self.worker.process_workflow_job(self.job_id), {'result': 'internal only'})

    def test_unclaimable_acknowledged_without_work(self):
        self.claim_workflow_job.return_value = None
        self.assertEqual(self.post().status_code, 204)
        self.download_cv.assert_not_called()
        self.workflow.assert_not_called()

    def test_duplicate_delivery_runs_once(self):
        self.claim_workflow_job.side_effect = [self.job, None]
        self.assertEqual(self.post().status_code, 204)
        self.assertEqual(self.post().status_code, 204)
        self.download_cv.assert_called_once()
        self.workflow.assert_awaited_once()

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


if __name__ == '__main__':
    unittest.main()
