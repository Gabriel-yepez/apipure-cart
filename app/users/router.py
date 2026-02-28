from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user_id
from app.users.schemas import UserOut, UserUpdate
from app.users import service

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_my_profile(user_id: str = Depends(get_current_user_id)):
    """Return the profile of the authenticated user."""
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/me", response_model=UserOut)
async def update_my_profile(
    body: UserUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Update the authenticated user's profile."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update",
        )
    updated = service.update_user(user_id, updates)
    return updated


@router.get("/{user_id}", response_model=UserOut)
async def get_user_by_id(
    user_id: str,
    _: str = Depends(get_current_user_id),
):
    """Get any user by ID (admin use)."""
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
