from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user_id
from app.orders import controller
from app.orders.models import OrderCreate, OrderOut, OrderSummaryOut, UpdateOrderStatus
from app.apiResponse.schemas import ApiResponse, create_response

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse[OrderOut],
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    body: OrderCreate,
    user_id: str = Depends(get_current_user_id),
):
    """
    Place a new order.
    Resolves current product prices (with discounts), creates the order and
    its line items, and saves the shipping address.
    """
    payload = body.model_dump()
    data = controller.create_order(user_id, payload)
    return create_response(data=data, messages="Order created successfully")


@router.get("", response_model=ApiResponse[list[OrderSummaryOut]])
async def list_my_orders(user_id: str = Depends(get_current_user_id)):
    """Return a summary list of all orders for the authenticated user."""
    data = controller.get_user_orders(user_id)
    return create_response(data=data, messages="Orders retrieved successfully")


@router.get("/{order_id}", response_model=ApiResponse[OrderOut])
async def get_order(
    order_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get full details of a specific order (user must be the owner)."""
    data = controller.get_order(order_id, user_id)
    return create_response(data=data, messages="Order retrieved successfully")


@router.put("/{order_id}/status", response_model=ApiResponse[OrderOut])
async def update_order_status(
    order_id: str,
    body: UpdateOrderStatus,
    _: str = Depends(get_current_user_id),
):
    """
    Update the status of an order.
    Typically called by admin/staff or by a gateway webhook handler.
    """
    data = controller.update_order_status(
        order_id,
        new_status=body.status.value,
        internal_notes=body.internal_notes,
    )
    return create_response(data=data, messages=f"Order status updated to '{body.status.value}'")


@router.post("/{order_id}/cancel", response_model=ApiResponse[OrderOut])
async def cancel_order(
    order_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    Cancel an order that is still pending.
    Only the order owner can cancel; orders already shipped cannot be cancelled.
    """
    data = controller.cancel_order(order_id, user_id)
    return create_response(data=data, messages="Order cancelled successfully")
