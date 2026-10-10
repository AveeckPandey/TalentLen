"""Supabase JWT authentication for FastAPI.

Local-dev friendly: if Supabase is not configured (no SUPABASE_URL and
REQUIRE_AUTH=False), all requests pass through as a local dev user so
existing CLI/tests/dashboard keep working with zero setup.

Supports both legacy (anon + JWT_SECRET HS256) and new
(publishable sb_publishable_... + JWKS RS256/ES256) Supabase Auth.
Verification order: JWKS -> HS256 secret -> Supabase Auth API.
"""

import logging
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from src.config import settings

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


class AuthUser(BaseModel):
    """Authenticated principal passed into route handlers."""

    id: str
    email: Optional[str] = None
    role: str = "authenticated"
    is_dev: bool = False


def is_auth_configured() -> bool:
    return bool(settings.SUPABASE_URL and (settings.frontend_key or settings.SUPABASE_JWT_SECRET))


def is_auth_enforced() -> bool:
    # Explicit REQUIRE_AUTH=True always enforces.
    if settings.REQUIRE_AUTH:
        return True
    # Auto-enforce once Supabase JWT secret is configured, unless the operator
    # explicitly sets REQUIRE_AUTH=False... default False keeps local dev open.
    # To auto-enforce in prod, set REQUIRE_AUTH=true in .env on Render.
    return False


def _dev_user() -> AuthUser:
    return AuthUser(id="local-dev", email="dev@localhost", is_dev=True)


def _verify_via_jwks(token: str) -> Optional[AuthUser]:
    """Verify with Supabase JWKS (new asymmetric keys). Returns None if not applicable."""
    jwks_url = settings.effective_jwks_url
    if not jwks_url or not settings.SUPABASE_URL:
        return None
    try:
        jwk_client = jwt.PyJWKClient(jwks_url)
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience="authenticated",
            issuer=f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1",
            options={"require": ["exp", "sub"]},
        )
        return AuthUser(
            id=str(payload.get("sub")),
            email=payload.get("email"),
            role=str(payload.get("role", "authenticated")),
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired, please sign in again")
    except Exception as e:
        logger.debug(f"JWKS verify skipped/failed: {e}")
        return None


def verify_supabase_token(token: str) -> AuthUser:
    """Verify a Supabase access token and return the principal."""
    # 1. JWKS (new sb_publishable_... keys)
    user = _verify_via_jwks(token)
    if user:
        return user

    # 2. Legacy HS256 secret
    secret = (settings.SUPABASE_JWT_SECRET or "").strip()
    if secret:
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience="authenticated",
                options={"require": ["exp", "sub"]},
            )
            return AuthUser(
                id=str(payload.get("sub")),
                email=payload.get("email"),
                role=str(payload.get("role", "authenticated")),
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired, please sign in again")
        except jwt.InvalidTokenError as e:
            logger.debug(f"JWT verify failed: {e}")
            pass

    # 3. Fallback: ask Supabase Auth API (costs 1 network call)
    if settings.SUPABASE_URL and settings.frontend_key:
        try:
            from supabase import create_client

            client = create_client(settings.SUPABASE_URL, settings.frontend_key)
            res = client.auth.get_user(token)
            user = res.user if hasattr(res, "user") else res.get("user") if isinstance(res, dict) else None
            if user is None:
                raise ValueError("no user")
            uid = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
            email = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else None)
            if not uid:
                raise ValueError("missing sub")
            return AuthUser(id=str(uid), email=email)
        except HTTPException:
            raise
        except Exception as e:
            logger.debug(f"Supabase get_user failed: {e}")

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")


async def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> AuthUser:
    """FastAPI dependency. Enforces auth only when REQUIRE_AUTH=true."""
    if not is_auth_enforced():
        # Open local-dev mode — but still accept + verify token if provided
        # so the dashboard works identically before/after login.
        if creds and creds.credentials:
            try:
                return verify_supabase_token(creds.credentials)
            except HTTPException:
                return _dev_user()
        return _dev_user()

    if not creds or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return verify_supabase_token(creds.credentials)


async def get_optional_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> AuthUser:
    """Never 401s. Used for public routes that just want user_id when logged in."""
    if creds and creds.credentials:
        try:
            return verify_supabase_token(creds.credentials)
        except HTTPException:
            pass
    if is_auth_enforced():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return _dev_user()
