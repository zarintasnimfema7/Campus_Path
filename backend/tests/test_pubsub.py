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
        self.assertEqual(pubsub.publish_workflow_job(self.job_id, 'user_A'), 'message-123')
        self.publisher.topic_path.assert_called_once_with('test-project', 'test-topic')
        args, kwargs = self.publisher.publish.call_args
        self.assertEqual(args, ('projects/test-project/topics/test-topic',))
        self.assertEqual(set(kwargs), {'data', 'ordering_key'})
        self.assertEqual(kwargs['ordering_key'], 'user_A')
        self.assertIsInstance(kwargs['data'], bytes)
        self.assertEqual(json.loads(kwargs['data']), {'job_id': self.job_id})
        self.future.result.assert_called_once_with()

    def test_lazy_client_reused_with_adc(self):
        self.client.assert_not_called()
        pubsub.publish_workflow_job(self.job_id, 'user_A')
        pubsub.publish_workflow_job(self.job_id, 'user_A')
        self.client.assert_called_once_with(publisher_options=pubsub.pubsub_v1.types.PublisherOptions(enable_message_ordering=True))

    def test_missing_configuration(self):
        for variable in ('GOOGLE_CLOUD_PROJECT', 'PUBSUB_TOPIC_ID'):
            with self.subTest(variable=variable), patch.dict(os.environ, {variable: ' '}):
                with self.assertRaisesRegex(RuntimeError, variable):
                    pubsub.publish_workflow_job(self.job_id, 'user_A')
        self.client.assert_not_called()

    def test_publish_and_acknowledgement_errors_propagate(self):
        for method in (self.publisher.publish, self.future.result):
            with self.subTest(method=method):
                error = RuntimeError('publish failed')
                method.side_effect = error
                with self.assertRaises(RuntimeError) as caught:
                    pubsub.publish_workflow_job(self.job_id, 'user_A')
                self.assertIs(caught.exception, error)
                method.side_effect = None

    def test_invalid_job_id_rejected(self):
        with self.assertRaises(ValueError):
            pubsub.publish_workflow_job('not-a-uuid', 'user_A')
        self.client.assert_not_called()

    def test_missing_ordering_key_rejected(self):
        for key in ('', ' ', None):
            with self.subTest(key=key), self.assertRaises(ValueError):
                pubsub.publish_workflow_job(self.job_id, key)
        with self.assertRaises(TypeError):
            pubsub.publish_workflow_job(self.job_id)
        self.client.assert_not_called()

    def test_same_and_different_user_keys(self):
        jobs = [self.job_id, '550e8400-e29b-41d4-a716-446655440001',
                '550e8400-e29b-41d4-a716-446655440002']
        for job, user in zip(jobs, ('user_A', 'user_A', 'user_B')):
            pubsub.publish_workflow_job(job, user)
        calls = self.publisher.publish.call_args_list
        self.assertEqual([call.kwargs['ordering_key'] for call in calls], ['user_A', 'user_A', 'user_B'])
        self.assertEqual([json.loads(call.kwargs['data']) for call in calls], [{'job_id': job} for job in jobs])


if __name__ == '__main__':
    unittest.main()
