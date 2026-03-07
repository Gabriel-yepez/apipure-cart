import logging
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

logger = logging.getLogger(__name__)


def register_user(email: str, password: str, full_name: str, role: str = "customer") -> TokenResponse:
    """Register a new user and return JWT tokens."""
    logger.info(f"Registering new user with email: {email} and role: {role}")
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
        .insert({"email": email, "hashed_password": hashed, "full_name": full_name, "role": role})
        .execute()
    )

    user_id = result.data[0]["id"]
    return TokenResponse(
        access_token=create_access_token(user_id, role),
        refresh_token=create_refresh_token(user_id),
        role=role,
    )


def login_user(email: str, password: str) -> TokenResponse:
    """Authenticate user and return JWT tokens."""
    logger.info(f"User login attempt: {email}")
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
        access_token=create_access_token(user["id"], user["role"]),
        refresh_token=create_refresh_token(user["id"]),
        role=user["role"],
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
    db = get_supabase()
    result = db.table("users").select("role").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    role = result.data[0]["role"]
    return TokenResponse(
        access_token=create_access_token(user_id, role),
        refresh_token=create_refresh_token(user_id),
        role=role,
    )
