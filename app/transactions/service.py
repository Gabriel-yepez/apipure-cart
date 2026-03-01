from app.database import get_supabase

TX_FIELDS = "id, user_id, status, total, payment_method, created_at"
TX_ITEM_FIELDS = "product_id, quantity, unit_price"


def create_transaction(user_id: str, payment_method: str, items: list[dict]) -> dict:
    """
    Creates a transaction with its items in Supabase.
    Each item dict must have: product_id, quantity, unit_price.
    """
    db = get_supabase()

    total = sum(i["quantity"] * i["unit_price"] for i in items)

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
        for item in items
    ]
    db.table("transaction_items").insert(tx_items).execute()

    # Increment sales_count for each product
    for item in items:
        db.rpc("increment_sales_count", {
            "p_product_id": item["product_id"],
            "p_quantity": item["quantity"],
        }).execute()

    transaction["items"] = items
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


def get_transaction(transaction_id: str) -> dict | None:
    db = get_supabase()
    result = (
        db.table("transactions")
        .select(f"{TX_FIELDS}, transaction_items({TX_ITEM_FIELDS})")
        .eq("id", transaction_id)
        .single()
        .execute()
    )
    if not result.data:
        return None
    row = result.data
    row["items"] = row.pop("transaction_items", [])
    return row


def update_transaction_status(transaction_id: str, new_status: str) -> dict:
    db = get_supabase()
    result = (
        db.table("transactions")
        .update({"status": new_status})
        .eq("id", transaction_id)
        .select(TX_FIELDS)
        .single()
        .execute()
    )
    return result.data


def get_product_price(product_id: str) -> float | None:
    db = get_supabase()
    result = (
        db.table("products")
        .select("price, discount_percent")
        .eq("id", product_id)
        .single()
        .execute()
    )
    if not result.data:
        return None
    row = result.data
    price = row["price"]
    discount = row.get("discount_percent", 0.0) or 0.0
    return round(price * (1 - discount / 100), 2)
