from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "customer"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    role: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class OAuthUrlResponse(BaseModel):
    url: str


class OAuthCallbackRequest(BaseModel):
    """Request body for exchanging a Supabase OAuth authorization code (PKCE) for app JWTs."""
    code: str
    code_verifier: str
