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
from app.config import settings
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
        if not user["hashed_password"]:
            a_logger.warning(f"Login failed: OAuth-only account attempted password login: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This account uses social login. Please sign in with your OAuth provider (e.g. Google).",
            )
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


def login_oauth(provider: str, code_challenge: str) -> str:
    """
    Generate OAuth login URL for given provider using Supabase Authorization Code + PKCE flow.

    The frontend is responsible for generating the code_verifier and code_challenge.
    We only forward the code_challenge to Supabase so it returns an authorization code
    instead of tokens in the URL fragment.
    """
    a_logger.info(f"OAuth login attempt for provider: {provider} (PKCE flow)")

    try:
        from app.config import settings as _settings
        from urllib.parse import urlencode

        base_url = _settings.SUPABASE_URL.rstrip("/")
        params = urlencode({
            "provider": provider,
            "redirect_to": _settings.OAUTH_REDIRECT_URL,
            "response_type": "code",
            "code_challenge": code_challenge,
            "code_challenge_method": "s256",
        })
        url = f"{base_url}/auth/v1/authorize?{params}"

        a_logger.info(f"OAuth authorization URL generated for {provider} (PKCE)")
        return url
    except Exception as e:
        a_logger.error(f"Unexpected error during OAuth login for {provider}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating OAuth URL for {provider}"
        )


def exchange_oauth_code(code: str, code_verifier: str) -> TokenResponse:
    """
    Exchange a Supabase OAuth authorization code + PKCE code_verifier for application JWTs.

    Flow (Authorization Code + PKCE):
    1. Send the authorization code + code_verifier to Supabase's token endpoint
       so Supabase can verify the PKCE challenge and return a session.
    2. Extract the Supabase access_token from the session.
    3. Use the access_token to retrieve the authenticated user from Supabase Auth.
    4. Look up (or create) the corresponding row in the custom `users` table.
    5. Return application-level JWT access + refresh tokens.
    """
    a_logger.info("Start OAuth code exchange (PKCE)")
    db = get_supabase()

    try:
        # 1. Exchange authorization code + code_verifier for a Supabase session.
        #    Try the SDK method first (supabase-py >= 2.10.0 with gotrue-py >= 2.9.0).
        #    Fall back to a raw HTTP call if the SDK method is unavailable.
        supabase_access_token: str | None = None

        try:
            session_response = db.auth.exchange_code_for_session(
                {"auth_code": code, "code_verifier": code_verifier}
            )
            session = session_response.session
            if session is None:
                a_logger.warning("OAuth code exchange failed: Supabase returned no session")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired authorization code",
                )
            supabase_access_token = session.access_token
            a_logger.info("Supabase session obtained via SDK exchange_code_for_session")
        except AttributeError:
            # SDK method not available — fall back to raw HTTP POST
            a_logger.info("SDK exchange_code_for_session not available, using raw HTTP fallback")
            import httpx

            token_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=pkce"
            headers = {
                "apikey": settings.SUPABASE_KEY,
                "Content-Type": "application/json",
            }
            payload = {
                "auth_code": code,
                "code_verifier": code_verifier,
            }

            resp = httpx.post(token_url, json=payload, headers=headers, timeout=15.0)

            if resp.status_code != 200:
                a_logger.warning(
                    f"Supabase token endpoint returned {resp.status_code}: {resp.text}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired authorization code",
                )

            token_data = resp.json()
            supabase_access_token = token_data.get("access_token")

            if not supabase_access_token:
                a_logger.warning("Supabase token response missing access_token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired authorization code",
                )
            a_logger.info("Supabase session obtained via raw HTTP token endpoint")

        # 2. Verify the Supabase access_token and retrieve the Supabase Auth user
        sb_user_response = db.auth.get_user(supabase_access_token)
        sb_user = sb_user_response.user

        if sb_user is None:
            a_logger.warning("OAuth code exchange failed: could not retrieve Supabase user")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OAuth token",
            )

        email = sb_user.email
        # Supabase user_metadata may include full_name or name depending on provider
        metadata = sb_user.user_metadata or {}
        full_name = (
            metadata.get("full_name")
            or metadata.get("name")
            or metadata.get("preferred_username")
            or email.split("@")[0]
        )
        avatar_url = metadata.get("avatar_url") or metadata.get("picture")

        a_logger.info(f"Supabase OAuth user verified: {email}")

        # 3. Find or create the user in the custom `users` table
        existing = db.table("users").select("id, role").eq("email", email).execute()

        if existing.data:
            # Existing user — update avatar if available and issue tokens
            user = existing.data[0]
            user_id = user["id"]
            role = user["role"]

            # Optionally update avatar_url if it was empty
            if avatar_url:
                db.table("users").update({"avatar_url": avatar_url}).eq("id", user_id).execute()

            a_logger.info(f"OAuth login for existing user: {email} (id: {user_id})")
        else:
            # New user — auto-register from OAuth data
            insert_data = {
                "email": email,
                "full_name": full_name,
                "role": "customer",
                "hashed_password": "",  # OAuth users have no password
            }
            if avatar_url:
                insert_data["avatar_url"] = avatar_url

            result = db.table("users").insert(insert_data).execute()
            user_id = result.data[0]["id"]
            role = "customer"
            a_logger.info(f"OAuth auto-registered new user: {email} (id: {user_id})")

        # 4. Issue app-level JWTs
        return TokenResponse(
            access_token=create_access_token(user_id, role),
            refresh_token=create_refresh_token(user_id),
            role=role,
        )

    except HTTPException:
        raise
    except Exception as e:
        a_logger.error(f"Unexpected error during OAuth code exchange: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exchanging OAuth authorization code",
        )
