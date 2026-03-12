from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_current_user_id
from app.products.models import ProductCreate, ProductUpdate, ProductOut
from app.products import controller
from app.apiResponse.schemas import ApiResponse, create_response

router = APIRouter()


# ─── Public endpoints ─────────────────────────────────────────────────────────

@router.get("", response_model=ApiResponse[list[ProductOut]])
async def list_products(
    category: str | None = Query(None),
    min_price: float | None = Query(None),
    max_price: float | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List products with optional filters."""
    products = controller.list_products(category, min_price, max_price, search, limit, offset)
    return create_response(data=products, messages="Products retrieved successfully")


@router.get("/discounted", response_model=ApiResponse[list[ProductOut]])
async def discounted_products(limit: int = Query(20, ge=1, le=100)):
    """Return products that have an active discount (discount_percent > 0)."""
    products = controller.get_discounted_products(limit)
    return create_response(data=products, messages="Discounted products retrieved successfully")


@router.get("/best-sellers", response_model=ApiResponse[list[ProductOut]])
async def best_sellers(limit: int = Query(20, ge=1, le=100)):
    """Return products ordered by sales count descending."""
    products = controller.get_best_sellers(limit)
    return create_response(data=products, messages="Best selling products retrieved successfully")


@router.get("/{product_id}", response_model=ApiResponse[ProductOut])
async def get_product(product_id: str):
    """Get a single product by ID."""
    product = controller.get_product(product_id)
    return create_response(data=product, messages="Product details retrieved successfully")


# ─── Protected (admin) endpoints ──────────────────────────────────────────────

@router.post("", response_model=ApiResponse[ProductOut], status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    _: str = Depends(get_current_user_id),
):
    """Create a new product."""
    product = controller.create_product(body.model_dump())
    return create_response(data=product, messages="Product created successfully")


@router.put("/{product_id}", response_model=ApiResponse[ProductOut])
async def update_product(
    product_id: str,
    body: ProductUpdate,
    _: str = Depends(get_current_user_id),
):
    """Update an existing product."""
    updates = body.model_dump(exclude_none=True)
    product = controller.update_product(product_id, updates)
    return create_response(data=product, messages="Product updated successfully")


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    _: str = Depends(get_current_user_id),
):
    """Delete (or deactivate) a product."""
    controller.delete_product(product_id)
    return
