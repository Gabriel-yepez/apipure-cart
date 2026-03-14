from fastapi import APIRouter, Query, status, HTTPException

from app.auth.models import LoginRequest, RegisterRequest, TokenResponse, RefreshRequest, OAuthUrlResponse, OAuthCallbackRequest
from app.auth import controller
from app.apiResponse.schemas import ApiResponse, create_response

router = APIRouter()


@router.post("/register", response_model=ApiResponse[TokenResponse], status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    """Register a new user and return JWT tokens."""
    data = controller.register_user(body.email, body.password, body.full_name, body.role)
    return create_response(data=data, messages="User registered successfully")


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(body: LoginRequest):
    """Authenticate user and return JWT tokens."""
    data = controller.login_user(body.email, body.password)
    return create_response(data=data, messages="Login successful")


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh_token(body: RefreshRequest):
    """Issue a new access token from a valid refresh token."""
    data = controller.refresh_tokens(body.refresh_token)
    return create_response(data=data, messages="Token refreshed successfully")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """
    Logout endpoint placeholder.
    With stateless JWTs the client just discards both tokens.
    """
    return


@router.get("/login/{provider}", response_model=ApiResponse[OAuthUrlResponse])
async def login_oauth(provider: str, code_challenge: str = Query(..., min_length=43, max_length=128)):
    """
    Generate an OAuth authorization URL for the given provider (Authorization Code + PKCE).

    The frontend must generate a code_verifier / code_challenge pair and send the
    code_challenge here. Supabase will return an authorization code (not tokens)
    to the redirect URL.
    """
    if provider not in ["google", "facebook", "twitter"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported provider")
    
    url = controller.login_oauth(provider, code_challenge)
    data = OAuthUrlResponse(url=url)
    return create_response(data=data, messages=f"OAuth URL for {provider} successfully generated")


@router.post("/oauth/callback", response_model=ApiResponse[TokenResponse])
async def oauth_callback(body: OAuthCallbackRequest):
    """
    Exchange a Supabase OAuth authorization code + PKCE code_verifier for application JWT tokens.

    The frontend calls this after receiving the authorization code from Supabase's redirect.
    """
    data = controller.exchange_oauth_code(body.code, body.code_verifier)
    return create_response(data=data, messages="OAuth login successful")
