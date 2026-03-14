from fastapi import HTTPException, status

from app.database import get_supabase
from app.trace.logger import logger

# ─── Field selects ────────────────────────────────────────────────────────────
ORDER_FIELDS = (
    "id, user_id, payment_method_id, gateway_payment_id, gateway_status, "
    "status, subtotal, discount_amount, shipping_cost, tax_amount, total, "
    "currency, coupon_code, customer_notes, paid_at, created_at, updated_at"
)
ORDER_ITEM_FIELDS = (
    "id, product_id, product_name, quantity, unit_price, discount_percent, line_total"
)
SHIPPING_FIELDS = (
    "id, order_id, recipient_name, phone, email, "
    "address_line1, address_line2, city, state, postal_code, country_code, "
    "carrier, tracking_number, tracking_url, shipping_status, "
    "estimated_delivery, shipped_at, delivered_at, created_at, updated_at"
)
PRODUCT_FIELDS = "id, name, price, discount_percent, stock"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_product(product_id: str) -> dict:
    """Fetch a product and raise 404 if not found or inactive."""
    db = get_supabase()
    result = (
        db.table("products")
        .select(PRODUCT_FIELDS)
        .eq("id", product_id)
        .eq("is_active", True)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found or inactive",
        )
    return result.data


def _validate_payment_method(method_id: str) -> None:
    """Raise 404 if the requested payment method does not exist or is inactive."""
    db = get_supabase()
    result = (
        db.table("payment_methods")
        .select("id")
        .eq("id", method_id)
        .eq("is_active", True)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or inactive payment method",
        )


def _build_order_out(order: dict, db) -> dict:
    """Attach items and shipping to an order dict."""
    items_result = (
        db.table("order_items")
        .select(ORDER_ITEM_FIELDS)
        .eq("order_id", order["id"])
        .execute()
    )
    order["items"] = items_result.data or []

    shipping_result = (
        db.table("shipping_details")
        .select(SHIPPING_FIELDS)
        .eq("order_id", order["id"])
        .single()
        .execute()
    )
    order["shipping"] = shipping_result.data  # may be None

    return order


# ─── Public functions ─────────────────────────────────────────────────────────

def create_order(user_id: str, payload: dict) -> dict:
    """
    Place a new order for a user.

    Steps:
      1. Validate payment method exists and is active.
      2. Fetch product prices (active products only), compute line totals.
      3. Insert the parent `orders` row.
      4. Insert `order_items` rows.
      5. Insert `shipping_details` row.
      6. Increment sales_count via existing RPC.
      7. Return full order with items and shipping.
    """
    db = get_supabase()
    logger.info(f"Creating order for user {user_id}")

    try:
        _validate_payment_method(payload["payment_method_id"])

        # Resolve prices and build line items
        items_in = payload["items"]  # list of {product_id, quantity}
        resolved_items: list[dict] = []
        subtotal = 0.0

        for item in items_in:
            product = _get_product(item["product_id"])
            unit_price = round(product["price"], 2)
            discount_pct = product.get("discount_percent") or 0.0
            line_total = round(
                item["quantity"] * unit_price * (1 - discount_pct / 100), 2
            )
            subtotal += line_total
            resolved_items.append({
                "product_id": item["product_id"],
                "product_name": product["name"],
                "quantity": item["quantity"],
                "unit_price": unit_price,
                "discount_percent": discount_pct,
                "line_total": line_total,
            })

        subtotal = round(subtotal, 2)
        shipping_cost = 0.0   # extend later with real shipping rate logic
        tax_amount = 0.0      # extend later with tax calculation
        discount_amount = 0.0 # extend later for coupon logic
        total = round(subtotal + shipping_cost + tax_amount - discount_amount, 2)

        # Insert order
        order_row = {
            "user_id": user_id,
            "payment_method_id": payload["payment_method_id"],
            "status": "pending",
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "shipping_cost": shipping_cost,
            "tax_amount": tax_amount,
            "total": total,
            "currency": payload.get("currency", "USD"),
            "coupon_code": payload.get("coupon_code"),
            "customer_notes": payload.get("customer_notes"),
        }
        order_result = (
            db.table("orders")
            .insert(order_row)
            .select(ORDER_FIELDS)
            .single()
            .execute()
        )
        order = order_result.data
        order_id = order["id"]

        # Insert order items
        order_items = [
            {**item, "order_id": order_id}
            for item in resolved_items
        ]
        db.table("order_items").insert(order_items).execute()

        # Insert shipping details
        shipping_in = payload["shipping"]
        shipping_in["order_id"] = order_id
        shipping_in["shipping_status"] = "pending"
        db.table("shipping_details").insert(shipping_in).execute()

        # Increment sales_count for each product (existing RPC)
        for item in resolved_items:
            db.rpc("increment_sales_count", {
                "p_product_id": item["product_id"],
                "p_quantity": item["quantity"],
            }).execute()

        logger.info(f"Order {order_id} created for user {user_id}")
        return _build_order_out(order, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating order for user {user_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create order",
        ) from e


def get_user_orders(user_id: str) -> list[dict]:
    """Return summary list of orders for a user (no items/shipping detail)."""
    db = get_supabase()
    try:
        result = (
            db.table("orders")
            .select(ORDER_FIELDS)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        orders = result.data or []
        # Attach item count from order_items
        for order in orders:
            items_res = (
                db.table("order_items")
                .select("id")
                .eq("order_id", order["id"])
                .execute()
            )
            order["item_count"] = len(items_res.data or [])
        return orders
    except Exception as e:
        logger.error(f"Error fetching orders for user {user_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve orders",
        ) from e


def get_order(order_id: str, user_id: str) -> dict:
    """
    Get a specific order by ID.
    Raises 404 if not found, 403 if it does not belong to the user.
    """
    db = get_supabase()
    try:
        result = (
            db.table("orders")
            .select(ORDER_FIELDS)
            .eq("id", order_id)
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        order = result.data
        if order["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        return _build_order_out(order, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {order_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve order",
        ) from e


def update_order_status(order_id: str, new_status: str, internal_notes: str | None = None) -> dict:
    """
    Update order status. Typically called by staff/admin or webhooks.
    Also sets `paid_at` when status transitions to 'paid'.
    """
    db = get_supabase()
    try:
        # Verify exists
        check = (
            db.table("orders")
            .select("id, user_id")
            .eq("id", order_id)
            .single()
            .execute()
        )
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        update_payload: dict = {"status": new_status}
        if internal_notes is not None:
            update_payload["internal_notes"] = internal_notes
        if new_status == "paid":
            from datetime import datetime, timezone
            update_payload["paid_at"] = datetime.now(timezone.utc).isoformat()

        result = (
            db.table("orders")
            .update(update_payload)
            .eq("id", order_id)
            .select(ORDER_FIELDS)
            .single()
            .execute()
        )
        order = result.data
        logger.info(f"Order {order_id} status updated to '{new_status}'")
        return _build_order_out(order, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order {order_id} status", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update order status",
        ) from e


def cancel_order(order_id: str, user_id: str) -> dict:
    """
    Cancel an order that is still in 'pending' or 'payment_pending' status.
    Only the owner can cancel.
    """
    db = get_supabase()
    try:
        order = get_order(order_id, user_id)
        if order["status"] not in ("pending", "payment_pending"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order in status '{order['status']}' cannot be cancelled",
            )
        result = (
            db.table("orders")
            .update({"status": "cancelled"})
            .eq("id", order_id)
            .select(ORDER_FIELDS)
            .single()
            .execute()
        )
        order = result.data
        logger.info(f"Order {order_id} cancelled by user {user_id}")
        return _build_order_out(order, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not cancel order",
        ) from e
