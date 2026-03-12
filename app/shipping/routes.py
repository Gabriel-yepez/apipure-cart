from fastapi import APIRouter, Depends

from app.dependencies import get_current_user_id
from app.shipping import controller
from app.shipping.models import UpdateShipping
from app.orders.models import ShippingOut
from app.apiResponse.schemas import ApiResponse, create_response

router = APIRouter()


@router.get("/{order_id}", response_model=ApiResponse[ShippingOut])
async def get_shipping(
    order_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get the shipping details for a specific order (owner only)."""
    data = controller.get_shipping(order_id, user_id)
    return create_response(data=data, messages="Shipping details retrieved successfully")


@router.patch("/{order_id}", response_model=ApiResponse[ShippingOut])
async def update_shipping(
    order_id: str,
    body: UpdateShipping,
    _: str = Depends(get_current_user_id),
):
    """
    Update tracking info for a shipment.
    Intended for staff/admin. Automatically timestamps shipped_at and
    delivered_at based on status transitions.
    """
    update_data = body.model_dump(exclude_unset=True)
    # Convert enum value to str for Supabase
    if "shipping_status" in update_data and update_data["shipping_status"] is not None:
        update_data["shipping_status"] = update_data["shipping_status"].value
    data = controller.update_shipping(order_id, update_data)
    return create_response(data=data, messages="Shipping details updated successfully")
