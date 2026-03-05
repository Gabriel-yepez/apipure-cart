from fastapi import APIRouter, Depends

from app.dependencies import get_current_user_id
from app.users.models import UserOut, UserUpdate
from app.users import controller

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_my_profile(user_id: str = Depends(get_current_user_id)):
    """Return the profile of the authenticated user."""
    return controller.get_user_profile(user_id)


@router.put("/me", response_model=UserOut)
async def update_my_profile(
    body: UserUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Update the authenticated user's profile."""
    updates = body.model_dump(exclude_none=True)
    return controller.update_user_profile(user_id, updates)


@router.get("/{user_id}", response_model=UserOut)
async def get_user_by_id(
    user_id: str,
    _: str = Depends(get_current_user_id),
):
    """Get any user by ID (admin use)."""
    return controller.get_user_profile(user_id)
