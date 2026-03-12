from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field

from app.orders.models import ShippingStatus


# ─── Shipping update (staff only) ────────────────────────────────────────────

class UpdateShipping(BaseModel):
    """Payload used by staff to update tracking info on a shipment."""
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    shipping_status: Optional[ShippingStatus] = None
    estimated_delivery: Optional[date] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
