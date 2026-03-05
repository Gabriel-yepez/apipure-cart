from fastapi import HTTPException, status

from app.database import get_supabase

FAVORITE_FIELDS = "id, user_id, product_id, created_at, products(id, name, price, discount_percent, image_url, sales_count)"


def get_user_favorites(user_id: str) -> list[dict]:
    db = get_supabase()
    result = (
        db.table("user_favorites")
        .select(FAVORITE_FIELDS)
        .eq("user_id", user_id)
        .execute()
    )
    return result.data


def add_favorite(user_id: str, product_id: str) -> dict:
    """Add a product to favorites, raising 409 if already exists."""
    if is_favorite(user_id, product_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is already in favorites",
        )
    db = get_supabase()
    result = (
        db.table("user_favorites")
        .insert({"user_id": user_id, "product_id": product_id})
        .select(FAVORITE_FIELDS)
        .single()
        .execute()
    )
    return result.data


def remove_favorite(user_id: str, product_id: str) -> None:
    """Remove a product from favorites, raising 404 if not found."""
    if not is_favorite(user_id, product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in favorites",
        )
    db = get_supabase()
    db.table("user_favorites").delete().eq("user_id", user_id).eq("product_id", product_id).execute()


def is_favorite(user_id: str, product_id: str) -> bool:
    db = get_supabase()
    result = (
        db.table("user_favorites")
        .select("id")
        .eq("user_id", user_id)
        .eq("product_id", product_id)
        .execute()
    )
    return bool(result.data)
