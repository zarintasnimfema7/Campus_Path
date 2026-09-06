import asyncio
import unittest

import httpx
from scripts.load_test import bounded_int, health_url, measure, percentile


class LoadToolTests(unittest.IsolatedAsyncioTestCase):
    def test_explicit_target_and_remote_guard(self):
        for target in [None, '', 'https://production.example', 'https://staging.example']:
            with self.assertRaises(ValueError):
                health_url(target)
        self.assertEqual(health_url('http://127.0.0.1:8000'), 'http://127.0.0.1:8000/health')
        self.assertEqual(health_url('http://[::1]:8000/'), 'http://[::1]:8000/health')
        self.assertEqual(health_url('https://staging.example', True), 'https://staging.example/health')

    def test_no_credentials_paths_redirect_modes_or_insecure_remote(self):
        for target in ['http://production.example', 'https://user:token@example.test',
                       'http://localhost/workflow/start', 'http://localhost?token=value',
                       'http://localhost#fragment', 'file:///tmp/test']:
            with self.assertRaises(ValueError):
                health_url(target, True)

    def test_bounded_configuration_and_percentiles(self):
        for value in [0, -1, 101, 'bad']:
            with self.assertRaises(ValueError):
                bounded_int(value, 100)
        self.assertEqual(percentile(list(range(1, 101)), .95), 95)
        self.assertEqual(percentile([10], .99), 10)

    async def test_counts_and_concurrency_without_network(self):
        active, maximum = 0, 0
        calls = []
        async def handle(request):
            nonlocal active, maximum
            active += 1
            maximum = max(maximum, active)
            calls.append(request)
            await asyncio.sleep(0)
            active -= 1
            return httpx.Response(200)
        result = await measure('http://localhost/health', 3, 10, transport=httpx.MockTransport(handle))
        self.assertEqual(result['total_requests'], 10)
        self.assertEqual(result['successes'], 10)
        self.assertEqual(result['failures'], 0)
        self.assertLessEqual(maximum, 3)
        self.assertTrue(all(r.method == 'GET' and r.url.path == '/health' for r in calls))
        self.assertLessEqual(result['p50_ms'], result['p95_ms'])
        self.assertLessEqual(result['p95_ms'], result['p99_ms'])

    async def test_errors_and_redirects_are_counted_without_retry_or_secret_output(self):
        calls = []
        def handle(request):
            calls.append(request)
            if len(calls) == 1:
                raise httpx.ConnectError('private token and host', request=request)
            return httpx.Response(302, headers={'Location': 'https://production.example'})
        result = await measure('http://localhost/health', 1, 2, 'private-token', transport=httpx.MockTransport(handle))
        self.assertEqual(len(calls), 2)
        self.assertEqual(result['failures'], 2)
        self.assertEqual(result['status_counts'], {'network_error': 1, '302': 1})
        self.assertNotIn('private', str(result))
