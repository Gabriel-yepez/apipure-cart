from fastapi import APIRouter, HTTPException, status

from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, RefreshRequest
from app.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.database import get_supabase

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    """Register a new user and return JWT tokens."""
    db = get_supabase()

    # Check if email already exists
    existing = db.table("users").select("id").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed = hash_password(body.password)
    result = (
        db.table("users")
        .insert({"email": body.email, "hashed_password": hashed, "full_name": body.full_name})
        .execute()
    )

    user_id = result.data[0]["id"]
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    """Authenticate user and return JWT tokens."""
    db = get_supabase()

    result = db.table("users").select("*").eq("email", body.email).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user = result.data[0]
    if not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return TokenResponse(
        access_token=create_access_token(user["id"]),
        refresh_token=create_refresh_token(user["id"]),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest):
    """Issue a new access token from a valid refresh token."""
    payload = verify_token(body.refresh_token, token_type="refresh")
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


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """
    Logout endpoint placeholder.
    With stateless JWTs the client just discards both tokens.
    For server-side blacklisting, store the JTI in a revoked-tokens table.
    """
    return
