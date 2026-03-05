from fastapi import HTTPException, status

from app.database import get_supabase
from app.products.models import ProductOut

PRODUCT_FIELDS = "id, name, description, price, discount_percent, stock, category, is_active, image_url, sales_count, created_at"


def list_products(
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[ProductOut]:
    db = get_supabase()
    query = db.table("products").select(PRODUCT_FIELDS).eq("is_active", True)

    if category:
        query = query.eq("category", category)
    if min_price is not None:
        query = query.gte("price", min_price)
    if max_price is not None:
        query = query.lte("price", max_price)
    if search:
        query = query.ilike("name", f"%{search}%")

    result = query.range(offset, offset + limit - 1).execute()
    return [ProductOut.from_db(r) for r in result.data]


def get_product(product_id: str) -> ProductOut:
    """Get a single product by ID."""
    db = get_supabase()
    result = (
        db.table("products")
        .select(PRODUCT_FIELDS)
        .eq("id", product_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return ProductOut.from_db(result.data)


def create_product(data: dict) -> ProductOut:
    db = get_supabase()
    result = db.table("products").insert(data).select(PRODUCT_FIELDS).single().execute()
    return ProductOut.from_db(result.data)


def update_product(product_id: str, data: dict) -> ProductOut:
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided",
        )
    # Verify product exists
    get_product(product_id)

    db = get_supabase()
    result = (
        db.table("products")
        .update(data)
        .eq("id", product_id)
        .select(PRODUCT_FIELDS)
        .single()
        .execute()
    )
    return ProductOut.from_db(result.data)


def delete_product(product_id: str) -> None:
    # Verify product exists
    get_product(product_id)

    db = get_supabase()
    db.table("products").delete().eq("id", product_id).execute()


def get_discounted_products(limit: int = 20) -> list[ProductOut]:
    db = get_supabase()
    result = (
        db.table("products")
        .select(PRODUCT_FIELDS)
        .eq("is_active", True)
        .gt("discount_percent", 0)
        .order("discount_percent", desc=True)
        .limit(limit)
        .execute()
    )
    return [ProductOut.from_db(r) for r in result.data]


def get_best_sellers(limit: int = 20) -> list[ProductOut]:
    db = get_supabase()
    result = (
        db.table("products")
        .select(PRODUCT_FIELDS)
        .eq("is_active", True)
        .order("sales_count", desc=True)
        .limit(limit)
        .execute()
    )
    return [ProductOut.from_db(r) for r in result.data]
