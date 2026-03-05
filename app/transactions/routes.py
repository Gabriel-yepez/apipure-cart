from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user_id
from app.transactions.models import TransactionCreate, TransactionOut, UpdateTransactionStatus
from app.transactions import controller

router = APIRouter()


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    body: TransactionCreate,
    user_id: str = Depends(get_current_user_id),
):
    """Create a new transaction/payment."""
    items = [{"product_id": item.product_id, "quantity": item.quantity} for item in body.items]
    return controller.create_transaction(user_id, body.payment_method, items)


@router.get("", response_model=list[TransactionOut])
async def list_my_transactions(user_id: str = Depends(get_current_user_id)):
    """Return all transactions for the authenticated user."""
    return controller.get_user_transactions(user_id)


@router.get("/{transaction_id}", response_model=TransactionOut)
async def get_transaction(
    transaction_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get a specific transaction by ID (user must own it)."""
    return controller.get_transaction(transaction_id, user_id)


@router.put("/{transaction_id}/status", response_model=TransactionOut)
async def update_status(
    transaction_id: str,
    body: UpdateTransactionStatus,
    _: str = Depends(get_current_user_id),
):
    """Update the status of a transaction."""
    return controller.update_transaction_status(transaction_id, body.status.value)
