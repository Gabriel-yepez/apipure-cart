from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user_id
from app.transactions.models import TransactionCreate, TransactionOut, UpdateTransactionStatus
from app.transactions import controller
from app.apiResponse.schemas import ApiResponse, create_response

router = APIRouter()


@router.post("", response_model=ApiResponse[TransactionOut], status_code=status.HTTP_201_CREATED)
async def create_transaction(
    body: TransactionCreate,
    user_id: str = Depends(get_current_user_id),
):
    """Create a new transaction/payment."""
    items = [{"product_id": item.product_id, "quantity": item.quantity} for item in body.items]
    data = controller.create_transaction(user_id, body.payment_method, items)
    return create_response(data=data, messages="Transaction created successfully")


@router.get("", response_model=ApiResponse[list[TransactionOut]])
async def list_my_transactions(user_id: str = Depends(get_current_user_id)):
    """Return all transactions for the authenticated user."""
    transactions = controller.get_user_transactions(user_id)
    return create_response(data=transactions, messages="Transactions retrieved successfully")


@router.get("/{transaction_id}", response_model=ApiResponse[TransactionOut])
async def get_transaction(
    transaction_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get a specific transaction by ID (user must own it)."""
    transaction = controller.get_transaction(transaction_id, user_id)
    return create_response(data=transaction, messages="Transaction details retrieved successfully")


@router.put("/{transaction_id}/status", response_model=ApiResponse[TransactionOut])
async def update_status(
    transaction_id: str,
    body: UpdateTransactionStatus,
    _: str = Depends(get_current_user_id),
):
    """Update the status of a transaction."""
    transaction = controller.update_transaction_status(transaction_id, body.status.value)
    return create_response(data=transaction, messages="Transaction status updated successfully")
