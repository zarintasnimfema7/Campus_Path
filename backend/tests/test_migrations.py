import unittest
from unittest.mock import patch

from scripts.check_migrations import check_migrations


class MigrationChecks(unittest.TestCase):
    def test_offline_sql_never_reads_credentials_or_opens_database(self):
        with patch('dotenv.dotenv_values', side_effect=AssertionError('Must not read local env')), \
             patch('sqlalchemy.create_engine', side_effect=AssertionError('Must not connect')), \
             patch('psycopg.connect', side_effect=AssertionError('Must not connect')):
            sql = check_migrations()
        self.assertIn('CREATE TABLE workflow_jobs', sql)
        self.assertIn('CREATE TABLE access_logs', sql)

    def test_multiple_heads_rejected(self):
        with patch('alembic.script.ScriptDirectory.get_heads', return_value=['a', 'b']):
            with self.assertRaisesRegex(RuntimeError, 'exactly one'):
                check_migrations()
