import os

from dotenv import load_dotenv
from psycopg_pool import ConnectionPool


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing from environment variables."
    )


pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=10,
    open=True,
)


def test_database_connection():
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT current_database(), current_user;"
            )

            return cursor.fetchone()