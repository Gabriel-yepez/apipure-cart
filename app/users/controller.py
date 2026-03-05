from fastapi import HTTPException, status

from app.database import get_supabase

USER_FIELDS = "id, email, full_name, avatar_url, role, created_at"


def get_user_profile(user_id: str) -> dict:
    """Get a user by ID, raising 404 if not found."""
    db = get_supabase()
    result = (
        db.table("users")
        .select(USER_FIELDS)
        .eq("id", user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return result.data


def update_user_profile(user_id: str, data: dict) -> dict:
    """Update a user's profile, raising 400 if no fields provided."""
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update",
        )
    db = get_supabase()
    result = (
        db.table("users")
        .update(data)
        .eq("id", user_id)
        .select(USER_FIELDS)
        .single()
        .execute()
    )
    return result.data
