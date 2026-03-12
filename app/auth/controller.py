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
from app.trace.logger import logger

# Use the app's logger scope
a_logger = logging.getLogger("apipure.auth")


def register_user(email: str, password: str, full_name: str, role: str = "customer") -> TokenResponse:
    """Register a new user and return JWT tokens."""
    a_logger.info(f"Start registration flow for email: {email} with role: {role}")
    db = get_supabase()

    try:
        # Check if email already exists
        existing = db.table("users").select("id").eq("email", email).execute()
        if existing.data:
            a_logger.warning(f"Registration failed: Email {email} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed = hash_password(password)
        a_logger.debug(f"Hashed password for {email}")
        
        result = (
            db.table("users")
            .insert({"email": email, "hashed_password": hashed, "full_name": full_name, "role": role})
            .execute()
        )

        user_id = result.data[0]["id"]
        a_logger.info(f"User registered successfully: {email} (id: {user_id})")
        
        return TokenResponse(
            access_token=create_access_token(user_id, role),
            refresh_token=create_refresh_token(user_id),
            role=role,
        )
    except HTTPException:
        raise
    except Exception as e:
        a_logger.error(f"Unexpected error during registration for {email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during user registration"
        )


def login_user(email: str, password: str) -> TokenResponse:
    """Authenticate user and return JWT tokens."""
    a_logger.info(f"Login attempt for email: {email}")
    db = get_supabase()

    try:
        result = db.table("users").select("*").eq("email", email).execute()
        
        if not result.data:
            a_logger.warning(f"Login failed: User not found with email: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        user = result.data[0]
        if not verify_password(password, user["hashed_password"]):
            a_logger.warning(f"Login failed: Incorrect password for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        a_logger.info(f"User login successful: {email} (role: {user['role']})")
        return TokenResponse(
            access_token=create_access_token(user["id"], user["role"]),
            refresh_token=create_refresh_token(user["id"]),
            role=user["role"],
        )
    except HTTPException:
        raise
    except Exception as e:
        a_logger.error(f"Unexpected error during login for {email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during login process"
        )


def refresh_tokens(refresh_token_str: str) -> TokenResponse:
    """Issue new tokens from a valid refresh token."""
    a_logger.info("Start token refresh process")
    
    payload = verify_token(refresh_token_str, token_type="refresh")
    if payload is None:
        a_logger.warning("Token refresh failed: Invalid or expired refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id: str = payload["sub"]
    db = get_supabase()
    
    try:
        result = db.table("users").select("role").eq("id", user_id).execute()
        if not result.data:
            a_logger.warning(f"Token refresh failed: User {user_id} not found in DB")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        role = result.data[0]["role"]
        a_logger.info(f"Token refreshed successfully for user_id: {user_id}")
        return TokenResponse(
            access_token=create_access_token(user_id, role),
            refresh_token=create_refresh_token(user_id),
            role=role,
        )
    except HTTPException:
        raise
    except Exception as e:
        a_logger.error(f"Unexpected error during token refresh for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during token refresh"
        )


def login_oauth(provider: str) -> str:
    """Generate OAuth login URL for given provider."""
    a_logger.info(f"OAuth login attempt for provider: {provider}")
    db = get_supabase()

    try:
        res = db.auth.sign_in_with_oauth({
            "provider": provider
        })
        url = res.url
        a_logger.info(f"OAuth authorization URL generated for {provider}")
        return url
    except Exception as e:
        a_logger.error(f"Unexpected error during OAuth login for {provider}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating OAuth URL for {provider}"
        )
