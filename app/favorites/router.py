from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user_id
from app.favorites import service

router = APIRouter()


@router.get("")
async def get_favorites(user_id: str = Depends(get_current_user_id)):
    """Return the list of favorite products for the authenticated user."""
    return service.get_user_favorites(user_id)


@router.post("/{product_id}", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    product_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Add a product to the user's favorites."""
    if service.is_favorite(user_id, product_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is already in favorites",
        )
    return service.add_favorite(user_id, product_id)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    product_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Remove a product from the user's favorites."""
    if not service.is_favorite(user_id, product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in favorites",
        )
    service.remove_favorite(user_id, product_id)
