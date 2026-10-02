from typing import Any, Dict, Optional
import jwt
from fastapi import HTTPException, status
from app.core.config import settings


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
    Raises HTTPException(401) on missing, expired, or malformed tokens.
    """
    if not token or not isinstance(token, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        if settings.SUPABASE_JWT_SECRET:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience=settings.SUPABASE_JWT_AUDIENCE,
                options={"verify_exp": True},
            )
        else:
            payload = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": True,
                },
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
