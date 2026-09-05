"""Alembic configuration independent of the application's database code."""
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from alembic.util import CommandError
from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def database_url():
    """Read backend/.env without changing it or exposing credentials."""
    value = dotenv_values(Path(__file__).resolve().parents[1] / '.env').get('DATABASE_URL')
    if not value:
        raise CommandError('DATABASE_URL is missing from backend/.env.')
    try:
        url = make_url(value)
        if url.drivername == 'postgresql':
            url = url.set(drivername='postgresql+psycopg')
        return url
    except Exception:
        raise CommandError('DATABASE_URL could not be parsed.') from None


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(), target_metadata=target_metadata,
        literal_binds=True, dialect_opts={'paramstyle': 'named'},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(database_url(), poolclass=NullPool)
    try:
        try:
            connection = connectable.connect()
        except Exception:
            # Driver errors can contain connection details; keep them private.
            raise CommandError(
                'Database connection failed. Check backend/.env and network access.'
            ) from None
        with connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
