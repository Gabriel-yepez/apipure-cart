from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_current_user_id
from app.products.models import ProductCreate, ProductUpdate, ProductOut
from app.products import controller

router = APIRouter()


# ─── Public endpoints ─────────────────────────────────────────────────────────

@router.get("", response_model=list[ProductOut])
async def list_products(
    category: str | None = Query(None),
    min_price: float | None = Query(None),
    max_price: float | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List products with optional filters."""
    return controller.list_products(category, min_price, max_price, search, limit, offset)


@router.get("/discounted", response_model=list[ProductOut])
async def discounted_products(limit: int = Query(20, ge=1, le=100)):
    """Return products that have an active discount (discount_percent > 0)."""
    return controller.get_discounted_products(limit)


@router.get("/best-sellers", response_model=list[ProductOut])
async def best_sellers(limit: int = Query(20, ge=1, le=100)):
    """Return products ordered by sales count descending."""
    return controller.get_best_sellers(limit)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: str):
    """Get a single product by ID."""
    return controller.get_product(product_id)


# ─── Protected (admin) endpoints ──────────────────────────────────────────────

@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    _: str = Depends(get_current_user_id),
):
    """Create a new product."""
    return controller.create_product(body.model_dump())


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: str,
    body: ProductUpdate,
    _: str = Depends(get_current_user_id),
):
    """Update an existing product."""
    updates = body.model_dump(exclude_none=True)
    return controller.update_product(product_id, updates)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    _: str = Depends(get_current_user_id),
):
    """Delete (or deactivate) a product."""
    controller.delete_product(product_id)
