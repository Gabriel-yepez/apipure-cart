from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class TransactionStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"


class TransactionItemIn(BaseModel):
    product_id: str
    quantity: int


class TransactionCreate(BaseModel):
    items: list[TransactionItemIn]
    payment_method: str  # e.g. "stripe", "paypal", "card"


class TransactionItemOut(BaseModel):
    product_id: str
    quantity: int
    unit_price: float


class TransactionOut(BaseModel):
    id: str
    user_id: str
    status: TransactionStatus
    total: float
    payment_method: str
    items: list[TransactionItemOut] = []
    created_at: datetime


class UpdateTransactionStatus(BaseModel):
    status: TransactionStatus
