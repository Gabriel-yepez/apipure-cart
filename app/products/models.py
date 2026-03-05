from datetime import datetime
from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
    description: str | None = None
    price: float
    discount_percent: float = 0.0  # 0-100
    stock: int = 0
    category: str | None = None
    is_active: bool = True
    image_url: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    discount_percent: float | None = None
    stock: int | None = None
    category: str | None = None
    is_active: bool | None = None
    image_url: str | None = None


class ProductOut(ProductBase):
    id: str
    sales_count: int = 0
    discounted_price: float | None = None  # computed
    created_at: datetime

    @classmethod
    def from_db(cls, row: dict) -> "ProductOut":
        discount = row.get("discount_percent", 0.0) or 0.0
        price = row.get("price", 0.0)
        discounted_price = round(price * (1 - discount / 100), 2) if discount > 0 else None
        return cls(**row, discounted_price=discounted_price)
