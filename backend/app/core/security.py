from typing import Any, Dict, Optional
import jwt
from jwt import PyJWKClient, PyJWKClientError
from fastapi import HTTPException, status
from app.core.config import settings

# Supabase publishes its asymmetric (e.g. ES256) signing keys as a JWKS set at
# https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json
_ES256_ALGORITHM = "ES256"
_JWKS_CACHE_LIFETIME_SECONDS = 600

_jwk_client: Optional[PyJWKClient] = None


def _configured_jwks_url() -> Optional[str]:
    if settings.SUPABASE_JWKS_URL:
        return str(settings.SUPABASE_JWKS_URL).strip()
    if settings.SUPABASE_URL:
        return f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
    return None


def _get_jwk_client() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        jwks_url = _configured_jwks_url()
        if not jwks_url:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication is temporarily unavailable: asymmetric signature verification is not configured.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        _jwk_client = PyJWKClient(
            jwks_url,
            cache_keys=True,
            lifespan=_JWKS_CACHE_LIFETIME_SECONDS,
        )
    return _jwk_client


class AuthenticatedUser:
    def __init__(
        self,
        user_id: str,
        email: Optional[str] = None,
        role: Optional[str] = None,
        app_metadata: Optional[Dict[str, Any]] = None,
        user_metadata: Optional[Dict[str, Any]] = None,
        raw_claims: Optional[Dict[str, Any]] = None,
    ):
        self.id = user_id
        self.email = email
        self.role = role
        self.app_metadata = app_metadata or {}
        self.user_metadata = user_metadata or {}
        self.raw_claims = raw_claims or {}

    @property
    def is_admin(self) -> bool:
        """
        Determine administrator authorization.
        Checks:
        1. Server-trusted app_metadata role claims (immutable to end users)
        2. Direct claims (e.g. is_admin)
        3. Server-side ADMIN_EMAILS allowlist
        """
        # 1. Check server-trusted app_metadata
        app_role = str(self.app_metadata.get("role", "")).strip().lower()
        if app_role in ["admin", "superadmin", "administrator"]:
            return True
        if self.app_metadata.get("is_admin") is True:
            return True
        if self.raw_claims.get("is_admin") is True:
            return True

        # 2. Check server-side ADMIN_EMAILS allowlist
        if self.email and settings.ADMIN_EMAILS:
            normalized_email = self.email.strip().lower()
            admin_emails = [e.strip().lower() for e in settings.ADMIN_EMAILS]
            if normalized_email in admin_emails:
                return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "is_admin": self.is_admin,
            "app_metadata": self.app_metadata,
        }


def verify_supabase_jwt(token: str) -> AuthenticatedUser:
    """
    Validate and decode a Supabase JWT token.

    Security policy: fail closed. Two verification strategies are supported,
    selected strictly by the token header's declared algorithm (the header is
    read only to route signature verification, and no claim is trusted before
    the signature validates):

    - ES256 (Supabase JWT signing keys): the signature is verified against the
      project's published JWKS public keys fetched from
      SUPABASE_JWKS_URL, defaulting to
      https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json. The
      key selection requires the token's `kid` header, and the same
      issuer/audience/expiration validation applies.
    - HS256 (Supabase legacy "JWT Secret"): retained only when
      SUPABASE_JWT_SECRET is intentionally configured, verified with the
      shared secret against the same issuer/audience/expiration rules.

    Tokens with any other algorithm (including "none") are rejected with 401.
    An empty/missing SUPABASE_JWT_SECRET only disables the legacy path; ES256
    verification via JWKS remains available once a project URL is configured.
    """
    if not token or not isinstance(token, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Read the header ONLY to choose the verification strategy; never trust
    # claims from an unverified token.
    try:
        header = jwt.get_unverified_header(token)
    except (jwt.DecodeError, jwt.exceptions.InvalidTokenError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    algorithm = header.get("alg")

    if algorithm == "HS256":
        if not settings.SUPABASE_JWT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token rejected: legacy HS256 verification is not configured for this project.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        signing_key = settings.SUPABASE_JWT_SECRET
        allowed_algorithms = ["HS256"]
    elif algorithm == _ES256_ALGORITHM:
        jwks_url = _configured_jwks_url()
        if not jwks_url:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token rejected: no JWKS signing-key source is configured to verify ES256 signatures.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_kid = header.get("kid")
        if not token_kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token rejected: ES256 token is missing its signing key identifier (kid).",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            signing_key = _get_jwk_client().get_signing_key_from_jwt(token).key
        except PyJWKClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token rejected: no trusted signing key matches kid '{token_kid}'. ({str(exc)})",
                headers={"WWW-Authenticate": "Bearer"},
            )
        allowed_algorithms = [_ES256_ALGORITHM]
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token signing algorithm '{algorithm}' is not supported. Only ES256 (signing keys) and HS256 (legacy secret) are accepted.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify expiration, audience, and (where a project URL is configured)
        # the Supabase issuer claim: Supabase tokens carry
        # "iss": "https://<project-ref>.supabase.co/auth/v1". When SUPABASE_URL
        # is set, tokens issued by any other project are rejected even if the
        # same keys/secret were somehow reused elsewhere.
        issuer = None
        if settings.SUPABASE_URL:
            issuer = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1"

        payload = jwt.decode(
            token,
            signing_key,
            algorithms=allowed_algorithms,
            audience=settings.SUPABASE_JWT_AUDIENCE,
            issuer=issuer,
            options={"verify_signature": True, "verify_exp": True},
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject (user ID)",
                headers={"WWW-Authenticate": "Bearer"},
            )

        email = payload.get("email")
        role = payload.get("role", "authenticated")
        app_metadata = payload.get("app_metadata", {})
        user_metadata = payload.get("user_metadata", {})

        return AuthenticatedUser(
            user_id=str(user_id),
            email=email,
            role=role,
            app_metadata=app_metadata,
            user_metadata=user_metadata,
            raw_claims=payload,
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.InvalidTokenError, jwt.DecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
