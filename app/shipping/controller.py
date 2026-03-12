from fastapi import HTTPException, status

from app.database import get_supabase
from app.trace.logger import logger

SHIPPING_FIELDS = (
    "id, order_id, recipient_name, phone, email, "
    "address_line1, address_line2, city, state, postal_code, country_code, "
    "carrier, tracking_number, tracking_url, shipping_status, "
    "estimated_delivery, shipped_at, delivered_at, created_at, updated_at"
)


def get_shipping(order_id: str, user_id: str) -> dict:
    """
    Return the shipping record for an order.
    Verifies that the order belongs to the requesting user.
    """
    db = get_supabase()
    try:
        # Ownership check via orders table
        order_result = (
            db.table("orders")
            .select("id, user_id")
            .eq("id", order_id)
            .single()
            .execute()
        )
        if not order_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        if order_result.data["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        result = (
            db.table("shipping_details")
            .select(SHIPPING_FIELDS)
            .eq("order_id", order_id)
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipping details not found for this order",
            )
        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching shipping for order {order_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve shipping details",
        ) from e


def update_shipping(order_id: str, update_data: dict) -> dict:
    """
    Update carrier/tracking info on a shipping record.
    Intended for staff/admin use. No ownership check (handled by router dependency).
    Auto-sets shipped_at when shipping_status transitions to 'picked_up' or later.
    """
    db = get_supabase()
    try:
        # Check record exists
        check = (
            db.table("shipping_details")
            .select("id, shipping_status")
            .eq("order_id", order_id)
            .single()
            .execute()
        )
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipping details not found for this order",
            )

        # Auto-timestamp shipped_at on first carrier handoff
        new_status = update_data.get("shipping_status")
        if new_status in ("picked_up", "in_transit") and not update_data.get("shipped_at"):
            from datetime import datetime, timezone
            update_data.setdefault("shipped_at", datetime.now(timezone.utc).isoformat())

        # Auto-timestamp delivered_at
        if new_status == "delivered" and not update_data.get("delivered_at"):
            from datetime import datetime, timezone
            update_data.setdefault("delivered_at", datetime.now(timezone.utc).isoformat())

        # Strip None values so we don't overwrite existing data
        clean_payload = {k: v for k, v in update_data.items() if v is not None}

        result = (
            db.table("shipping_details")
            .update(clean_payload)
            .eq("order_id", order_id)
            .select(SHIPPING_FIELDS)
            .single()
            .execute()
        )
        logger.info(f"Shipping for order {order_id} updated: {clean_payload}")
        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating shipping for order {order_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update shipping details",
        ) from e
