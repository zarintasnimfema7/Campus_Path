from app.database.supabase import supabase


def ensure_user_exists(
    user_id: str,
    email: str | None = None,
    name: str | None = None,
):
    existing = (
        supabase
        .table("users")
        .select("id")
        .eq("id", user_id)
        .execute()
    )

    if existing.data:
        return existing.data[0]

    payload = {
        "id": user_id,
    }

    if email:
        payload["email"] = email

    if name:
        payload["name"] = name

    result = (
        supabase
        .table("users")
        .insert(payload)
        .execute()
    )

    return result.data[0]