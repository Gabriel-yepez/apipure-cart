from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ─── Payment Method ──────────────────────────────────────────────────────────

class PaymentMethodOut(BaseModel):
    id: str
    name: str
    label: str
    provider: str
    is_active: bool
    created_at: datetime
