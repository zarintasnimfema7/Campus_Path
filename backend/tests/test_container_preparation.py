import importlib
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

BACKEND = Path(__file__).resolve().parents[1]


class ContainerPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch('dotenv.load_dotenv'), patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'CLERK_SECRET_KEY': 'test-only', 'GEMINI_API_KEY': 'test-only',
            'SERVICE_ROLE': 'api',
        }), patch('psycopg_pool.ConnectionPool'):
            cls.main = importlib.import_module('app.main')

    def client(self, role):
        with patch.dict(os.environ):
            if role is None:
                os.environ.pop('SERVICE_ROLE', None)
            else:
                os.environ['SERVICE_ROLE'] = role
            return TestClient(self.main.create_app())

    def test_api_and_default_routes(self):
        for role in ['api', None]:
            with self.subTest(role=role), self.client(role) as client:
                self.assertEqual(client.get('/health').status_code, 200)
                self.assertEqual(client.get('/docs').status_code, 200)
                paths = client.get('/openapi.json').json()['paths']
                self.assertIn('/workflow/start', paths)
                self.assertIn('/data/profiles', paths)
                self.assertEqual(client.post('/internal/workflow-jobs/process', json={}).status_code, 404)

    def test_worker_routes_and_harmless_request(self):
        with self.client('worker') as client, patch('app.routes.workflow_worker.process_workflow_job') as process:
            self.assertEqual(client.get('/health').status_code, 200)
            self.assertEqual(client.post('/internal/workflow-jobs/process', json={}).status_code, 400)
            process.assert_not_called()
            for path in ['/workflow/start', '/data/profiles', '/evidence/verify-github']:
                self.assertEqual(client.post(path, json={}).status_code, 404)
            for path in ['/docs', '/openapi.json', '/database/health', '/']:
                self.assertEqual(client.get(path).status_code, 404)

    def test_invalid_roles_fail_clearly(self):
        for role in ['', 'API', 'invalid']:
            with patch.dict(os.environ, {'SERVICE_ROLE': role}), self.assertRaisesRegex(ValueError, "SERVICE_ROLE must be 'api' or 'worker'"):
                self.main.create_app()

    def test_health_does_not_access_database_or_worker(self):
        for role in ['api', 'worker']:
            with self.client(role) as client, patch('app.database.neon.pool') as pool, patch('app.routes.workflow_worker.process_workflow_job') as process:
                self.assertEqual(client.get('/health').json()['status'], 'ok')
                pool.connection.assert_not_called()
                process.assert_not_called()

    def test_no_duplicate_requirement_packages(self):
        names = []
        for line in (BACKEND / 'requirements.txt').read_text(encoding='utf-8').splitlines():
            if line.strip() and not line.lstrip().startswith('#'):
                names.append(canonicalize_name(Requirement(line).name))
        self.assertEqual(len(names), len(set(names)))

    def test_static_container_contract(self):
        dockerfile = (BACKEND / 'Dockerfile').read_text()
        script = (BACKEND / 'entrypoint.sh').read_bytes()
        ignore = (BACKEND / '.dockerignore').read_text()
        self.assertIn('FROM python:3.12-slim', dockerfile)
        self.assertIn('USER campuspath:campuspath', dockerfile)
        self.assertLess(dockerfile.index('COPY requirements.txt'), dockerfile.index('COPY app/'))
        self.assertIn('pip install --no-cache-dir -r requirements.txt', dockerfile)
        self.assertNotIn('COPY . .', dockerfile)
        self.assertTrue(script.startswith(b'#!/bin/sh\nset -eu\n'))
        self.assertNotIn(b'\r', script)
        self.assertIn(b'exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"', script)
        self.assertNotIn('--reload', dockerfile + script.decode())
        self.assertIn('backend/entrypoint.sh text eol=lf', (BACKEND.parent / '.gitattributes').read_text())
        for pattern in ['.env', '.venv', '.git', '**/*credentials*.json', '**/*service-account*.json', '**/*.key', '**/*.pem']:
            self.assertIn(pattern, ignore.splitlines())
        self.assertNotIn('GOOGLE_APPLICATION_CREDENTIALS=', dockerfile)


if __name__ == '__main__':
    unittest.main()
