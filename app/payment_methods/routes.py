from fastapi import APIRouter

from app.payment_methods import controller
from app.payment_methods.models import PaymentMethodOut
from app.apiResponse.schemas import ApiResponse, create_response

router = APIRouter()


@router.get("", response_model=ApiResponse[list[PaymentMethodOut]])
async def list_payment_methods():
    """List all active payment methods available for checkout."""
    data = controller.list_payment_methods()
    return create_response(data=data, messages="Payment methods retrieved successfully")


@router.get("/{method_id}", response_model=ApiResponse[PaymentMethodOut])
async def get_payment_method(method_id: str):
    """Get a single payment method by ID."""
    data = controller.get_payment_method(method_id)
    return create_response(data=data, messages="Payment method retrieved successfully")
