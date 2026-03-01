from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user_id
from app.transactions.schemas import TransactionCreate, TransactionOut, UpdateTransactionStatus
from app.transactions import service

router = APIRouter()


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    body: TransactionCreate,
    user_id: str = Depends(get_current_user_id),
):
    """
    Create a new transaction/payment.
    Resolves current prices (with discounts) from the products table.
    """
    items_with_price = []
    for item in body.items:
        unit_price = service.get_product_price(item.product_id)
        if unit_price is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found",
            )
        items_with_price.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": unit_price,
        })

    transaction = service.create_transaction(user_id, body.payment_method, items_with_price)
    return transaction


@router.get("", response_model=list[TransactionOut])
async def list_my_transactions(user_id: str = Depends(get_current_user_id)):
    """Return all transactions for the authenticated user."""
    return service.get_user_transactions(user_id)


@router.get("/{transaction_id}", response_model=TransactionOut)
async def get_transaction(
    transaction_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get a specific transaction by ID (user must own it)."""
    transaction = service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if transaction["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return transaction


@router.put("/{transaction_id}/status", response_model=TransactionOut)
async def update_status(
    transaction_id: str,
    body: UpdateTransactionStatus,
    _: str = Depends(get_current_user_id),
):
    """
    Update the status of a transaction.
    Typically called from a payment gateway webhook.
    """
    transaction = service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    updated = service.update_transaction_status(transaction_id, body.status.value)
    updated["items"] = transaction.get("items", [])
    return updated
