import json
import os
import unittest
from unittest.mock import patch

from app.services import pubsub


class PubsubTests(unittest.TestCase):
    def setUp(self):
        pubsub._publisher.cache_clear()
        self.addCleanup(pubsub._publisher.cache_clear)
        env = patch.dict(os.environ, {'GOOGLE_CLOUD_PROJECT': 'test-project', 'PUBSUB_TOPIC_ID': 'test-topic'})
        env.start()
        self.addCleanup(env.stop)
        client = patch.object(pubsub.pubsub_v1, 'PublisherClient')
        self.client = client.start()
        self.addCleanup(client.stop)
        self.publisher = self.client.return_value
        self.publisher.topic_path.return_value = 'projects/test-project/topics/test-topic'
        self.future = self.publisher.publish.return_value
        self.future.result.return_value = 'message-123'
        self.job_id = '550e8400-e29b-41d4-a716-446655440000'

    def test_payload_topic_acknowledgement_and_message_id(self):
        self.assertEqual(pubsub.publish_workflow_job(self.job_id), 'message-123')
        self.publisher.topic_path.assert_called_once_with('test-project', 'test-topic')
        args, kwargs = self.publisher.publish.call_args
        self.assertEqual(args, ('projects/test-project/topics/test-topic',))
        self.assertEqual(set(kwargs), {'data'})
        self.assertIsInstance(kwargs['data'], bytes)
        self.assertEqual(json.loads(kwargs['data']), {'job_id': self.job_id})
        self.future.result.assert_called_once_with()

    def test_lazy_client_reused_with_adc(self):
        self.client.assert_not_called()
        pubsub.publish_workflow_job(self.job_id)
        pubsub.publish_workflow_job(self.job_id)
        self.client.assert_called_once_with()

    def test_missing_configuration(self):
        for variable in ('GOOGLE_CLOUD_PROJECT', 'PUBSUB_TOPIC_ID'):
            with self.subTest(variable=variable), patch.dict(os.environ, {variable: ' '}):
                with self.assertRaisesRegex(RuntimeError, variable):
                    pubsub.publish_workflow_job(self.job_id)
        self.client.assert_not_called()

    def test_publish_and_acknowledgement_errors_propagate(self):
        for method in (self.publisher.publish, self.future.result):
            with self.subTest(method=method):
                error = RuntimeError('publish failed')
                method.side_effect = error
                with self.assertRaises(RuntimeError) as caught:
                    pubsub.publish_workflow_job(self.job_id)
                self.assertIs(caught.exception, error)
                method.side_effect = None

    def test_invalid_job_id_rejected(self):
        with self.assertRaises(ValueError):
            pubsub.publish_workflow_job('not-a-uuid')
        self.client.assert_not_called()


if __name__ == '__main__':
    unittest.main()
