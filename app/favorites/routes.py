from typing import Any
from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user_id
from app.favorites import controller
from app.apiResponse.schemas import ApiResponse, create_response

router = APIRouter()


@router.get("", response_model=ApiResponse[list[Any]])
async def get_favorites(user_id: str = Depends(get_current_user_id)):
    """Return the list of favorite products for the authenticated user."""
    favorites = controller.get_user_favorites(user_id)
    return create_response(data=favorites, messages="Favorites retrieved successfully")


@router.post("/{product_id}", response_model=ApiResponse[Any], status_code=status.HTTP_201_CREATED)
async def add_favorite(
    product_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Add a product to the user's favorites."""
    data = controller.add_favorite(user_id, product_id)
    return create_response(data=data, messages="Product added to favorites")


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    product_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Remove a product from the user's favorites."""
    controller.remove_favorite(user_id, product_id)
    return
