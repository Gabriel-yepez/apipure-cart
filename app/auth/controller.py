from fastapi import HTTPException, status

from app.auth.models import TokenResponse
from app.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.database import get_supabase


def register_user(email: str, password: str, full_name: str) -> TokenResponse:
    """Register a new user and return JWT tokens."""
    db = get_supabase()

    # Check if email already exists
    existing = db.table("users").select("id").eq("email", email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed = hash_password(password)
    result = (
        db.table("users")
        .insert({"email": email, "hashed_password": hashed, "full_name": full_name})
        .execute()
    )

    user_id = result.data[0]["id"]
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


def login_user(email: str, password: str) -> TokenResponse:
    """Authenticate user and return JWT tokens."""
    db = get_supabase()

    result = db.table("users").select("*").eq("email", email).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user = result.data[0]
    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return TokenResponse(
        access_token=create_access_token(user["id"]),
        refresh_token=create_refresh_token(user["id"]),
    )


def refresh_tokens(refresh_token_str: str) -> TokenResponse:
    """Issue new tokens from a valid refresh token."""
    payload = verify_token(refresh_token_str, token_type="refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id: str = payload["sub"]
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )
