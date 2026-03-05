from fastapi import APIRouter, status

from app.auth.models import LoginRequest, RegisterRequest, TokenResponse, RefreshRequest
from app.auth import controller

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    """Register a new user and return JWT tokens."""
    return controller.register_user(body.email, body.password, body.full_name)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    """Authenticate user and return JWT tokens."""
    return controller.login_user(body.email, body.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest):
    """Issue a new access token from a valid refresh token."""
    return controller.refresh_tokens(body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """
    Logout endpoint placeholder.
    With stateless JWTs the client just discards both tokens.
    """
    return
