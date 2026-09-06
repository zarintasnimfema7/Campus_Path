"""Import the revision graph and render PostgreSQL SQL without reading credentials."""
import ast
from io import StringIO
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


def check_migrations():
    backend = Path(__file__).resolve().parents[1]
    output = StringIO()
    config = Config(str(backend / 'alembic.ini'), output_buffer=output)
    scripts = ScriptDirectory.from_config(config)
    heads = scripts.get_heads()
    if len(heads) != 1:
        raise RuntimeError(f'Expected exactly one Alembic head; found {len(heads)}.')
    revisions = list(scripts.walk_revisions())
    for revision in revisions:
        ast.parse(Path(revision.path).read_text(encoding='utf-8'))
        if not callable(revision.module.upgrade) or not callable(revision.module.downgrade):
            raise RuntimeError('Migration must provide upgrade and downgrade functions.')
    # sql=True invokes only run_migrations_offline; no application imports or DB URL.
    command.upgrade(config, 'head', sql=True)
    sql = output.getvalue()
    if not sql.strip() or 'CREATE TABLE' not in sql:
        raise RuntimeError('Offline migration SQL is unexpectedly empty.')
    print(f'Alembic validation passed: {len(revisions)} revisions, one head ({heads[0]}), offline SQL generated.')
    return sql


if __name__ == '__main__':
    check_migrations()
