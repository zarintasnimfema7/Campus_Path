from psycopg.rows import dict_row

from app.database.neon import pool


def ensure_user_exists(
    user_id: str,
    email: str | None = None,
    name: str | None = None,
):
    """
    Create the user if they do not exist.
    Otherwise update available user information.
    """

    query = """
        INSERT INTO users (
            id,
            email,
            name
        )
        VALUES (%s, %s, %s)

        ON CONFLICT (id)
        DO UPDATE SET
            email = COALESCE(EXCLUDED.email, users.email),
            name = COALESCE(EXCLUDED.name, users.name),
            updated_at = NOW()

        RETURNING
            id,
            email,
            name,
            github_username,
            created_at,
            updated_at;
    """

    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                query,
                (
                    user_id,
                    email,
                    name,
                ),
            )

            user = cursor.fetchone()

        conn.commit()

    return user