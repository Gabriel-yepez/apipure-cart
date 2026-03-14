from datetime import datetime, date
from enum import Enum
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


# ─── Enums ───────────────────────────────────────────────────────────────────

class OrderStatus(str, Enum):
    pending             = "pending"
    payment_pending     = "payment_pending"
    paid                = "paid"
    processing          = "processing"
    shipped             = "shipped"
    delivered           = "delivered"
    cancelled           = "cancelled"
    refunded            = "refunded"
    partially_refunded  = "partially_refunded"


class ShippingStatus(str, Enum):
    pending             = "pending"
    label_created       = "label_created"
    picked_up           = "picked_up"
    in_transit          = "in_transit"
    out_for_delivery    = "out_for_delivery"
    delivered           = "delivered"
    failed_attempt      = "failed_attempt"
    returned            = "returned"


# ─── Order Item schemas ───────────────────────────────────────────────────────

class OrderItemIn(BaseModel):
    """One product line when creating an order."""
    product_id: str
    quantity: int = Field(gt=0)


class OrderItemOut(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    discount_percent: float
    line_total: float


# ─── Shipping ─────────────────────────────────────────────────────────────────

class ShippingIn(BaseModel):
    """Shipping address provided by the customer at checkout."""
    recipient_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: str
    country_code: str = Field(min_length=2, max_length=2)

    @field_validator("country_code")
    @classmethod
    def uppercase_country(cls, v: str) -> str:
        return v.upper()


class ShippingOut(BaseModel):
    id: str
    order_id: str
    recipient_name: str
    phone: Optional[str]
    email: Optional[str]
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: Optional[str]
    postal_code: str
    country_code: str
    carrier: Optional[str]
    tracking_number: Optional[str]
    tracking_url: Optional[str]
    shipping_status: ShippingStatus
    estimated_delivery: Optional[date]
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ─── Order schemas ────────────────────────────────────────────────────────────

class OrderCreate(BaseModel):
    """Payload sent by the client to place a new order."""
    payment_method_id: str
    items: list[OrderItemIn] = Field(min_length=1)
    shipping: ShippingIn
    coupon_code: Optional[str] = None
    customer_notes: Optional[str] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        return v.upper()


class OrderOut(BaseModel):
    id: str
    user_id: str
    payment_method_id: str
    gateway_payment_id: Optional[str]
    gateway_status: Optional[str]
    status: OrderStatus
    subtotal: float
    discount_amount: float
    shipping_cost: float
    tax_amount: float
    total: float
    currency: str
    coupon_code: Optional[str]
    customer_notes: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemOut] = []
    shipping: Optional[ShippingOut] = None


class UpdateOrderStatus(BaseModel):
    status: OrderStatus
    internal_notes: Optional[str] = None


class OrderSummaryOut(BaseModel):
    """Lightweight order card for list views."""
    id: str
    status: OrderStatus
    total: float
    currency: str
    created_at: datetime
    item_count: int
