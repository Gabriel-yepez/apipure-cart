from app.database import get_supabase


def get_user_by_id(user_id: str) -> dict | None:
    db = get_supabase()
    result = (
        db.table("users")
        .select("id, email, full_name, avatar_url, role, created_at")
        .eq("id", user_id)
        .single()
        .execute()
    )
    return result.data


def update_user(user_id: str, data: dict) -> dict:
    db = get_supabase()
    result = (
        db.table("users")
        .update(data)
        .eq("id", user_id)
        .select("id, email, full_name, avatar_url, role, created_at")
        .single()
        .execute()
    )
    return result.data
