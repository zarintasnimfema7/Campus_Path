from pathlib import Path
import unittest

import yaml


class CiConfigurationTests(unittest.TestCase):
    def test_workflow_structure_and_non_deployment_boundary(self):
        root = Path(__file__).resolve().parents[2]
        # BaseLoader preserves GitHub's YAML `on` key instead of YAML 1.1 booleans.
        workflow = yaml.load((root / '.github/workflows/ci.yml').read_text(), Loader=yaml.BaseLoader)
        self.assertIn('pull_request', workflow['on'])
        self.assertTrue({'main', 'dev', 'feature'} <= set(workflow['on']['push']['branches']))
        self.assertEqual(workflow['permissions'], {'contents': 'read'})
        self.assertEqual(workflow['concurrency']['cancel-in-progress'], 'true')
        self.assertEqual(set(workflow['jobs']), {'backend', 'frontend', 'migrations', 'docker'})
        commands = []
        for job in workflow['jobs'].values():
            self.assertIn('timeout-minutes', job)
            for step in job['steps']:
                self.assertNotIn('continue-on-error', step)
                if step.get('uses', '').startswith('actions/checkout@'):
                    self.assertEqual(step['with']['persist-credentials'], 'false')
                commands.append(step.get('run', ''))
        for forbidden in ['docker push', 'gcloud ', 'alembic upgrade head', 'vercel ', 'secrets.']:
            self.assertNotIn(forbidden, '\n'.join(commands))
        self.assertIn('docker build -t campuspath-backend:ci ./backend', commands)
        self.assertIn('python -m unittest discover -s tests -q', commands)
        self.assertIn('npm ci', commands)
        self.assertIn('npm run lint', commands)
        self.assertIn('npm run build', commands)

    def test_frontend_ci_fixture_is_public_and_nonfunctional(self):
        import base64
        root = Path(__file__).resolve().parents[2]
        workflow = yaml.load((root / '.github/workflows/ci.yml').read_text(), Loader=yaml.BaseLoader)
        env = workflow['jobs']['frontend']['env']
        key = env['NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY']
        decoded = base64.b64decode(key.removeprefix('pk_test_') + '===').decode()
        self.assertEqual(decoded, 'ci.clerk.invalid$')
        self.assertNotIn('CLERK_SECRET_KEY', env)
