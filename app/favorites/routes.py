from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user_id
from app.favorites import controller

router = APIRouter()


@router.get("")
async def get_favorites(user_id: str = Depends(get_current_user_id)):
    """Return the list of favorite products for the authenticated user."""
    return controller.get_user_favorites(user_id)


@router.post("/{product_id}", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    product_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Add a product to the user's favorites."""
    return controller.add_favorite(user_id, product_id)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    product_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Remove a product from the user's favorites."""
    controller.remove_favorite(user_id, product_id)
