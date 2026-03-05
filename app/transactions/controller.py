from fastapi import HTTPException, status

from app.database import get_supabase

TX_FIELDS = "id, user_id, status, total, payment_method, created_at"
TX_ITEM_FIELDS = "product_id, quantity, unit_price"


def get_product_price(product_id: str) -> float:
    """Get the effective price of a product (with discount applied)."""
    db = get_supabase()
    result = (
        db.table("products")
        .select("price, discount_percent")
        .eq("id", product_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    row = result.data
    price = row["price"]
    discount = row.get("discount_percent", 0.0) or 0.0
    return round(price * (1 - discount / 100), 2)


def create_transaction(user_id: str, payment_method: str, items: list[dict]) -> dict:
    """
    Creates a transaction with its items in Supabase.
    Resolves current prices (with discounts) from the products table.
    """
    db = get_supabase()

    # Resolve prices
    items_with_price = []
    for item in items:
        unit_price = get_product_price(item["product_id"])
        items_with_price.append({
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price": unit_price,
        })

    total = sum(i["quantity"] * i["unit_price"] for i in items_with_price)

    # Insert parent transaction
    tx_result = (
        db.table("transactions")
        .insert({
            "user_id": user_id,
            "status": "pending",
            "total": total,
            "payment_method": payment_method,
        })
        .select(TX_FIELDS)
        .single()
        .execute()
    )
    transaction = tx_result.data

    # Insert transaction items
    tx_items = [
        {
            "transaction_id": transaction["id"],
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
        }
        for item in items_with_price
    ]
    db.table("transaction_items").insert(tx_items).execute()

    # Increment sales_count for each product
    for item in items_with_price:
        db.rpc("increment_sales_count", {
            "p_product_id": item["product_id"],
            "p_quantity": item["quantity"],
        }).execute()

    transaction["items"] = items_with_price
    return transaction


def get_user_transactions(user_id: str) -> list[dict]:
    db = get_supabase()
    result = (
        db.table("transactions")
        .select(f"{TX_FIELDS}, transaction_items({TX_ITEM_FIELDS})")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    rows = result.data
    for row in rows:
        row["items"] = row.pop("transaction_items", [])
    return rows


def get_transaction(transaction_id: str, user_id: str) -> dict:
    """Get a specific transaction by ID, verifying ownership."""
    db = get_supabase()
    result = (
        db.table("transactions")
        .select(f"{TX_FIELDS}, transaction_items({TX_ITEM_FIELDS})")
        .eq("id", transaction_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    row = result.data
    if row["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    row["items"] = row.pop("transaction_items", [])
    return row


def update_transaction_status(transaction_id: str, new_status: str) -> dict:
    """Update the status of a transaction."""
    db = get_supabase()

    # Verify transaction exists
    check = (
        db.table("transactions")
        .select(f"{TX_FIELDS}, transaction_items({TX_ITEM_FIELDS})")
        .eq("id", transaction_id)
        .single()
        .execute()
    )
    if not check.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    result = (
        db.table("transactions")
        .update({"status": new_status})
        .eq("id", transaction_id)
        .select(TX_FIELDS)
        .single()
        .execute()
    )
    updated = result.data
    updated["items"] = check.data.get("transaction_items", [])
    return updated
