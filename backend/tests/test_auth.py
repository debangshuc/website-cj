from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_current_user, require_admin
from app.core.config import settings

client = TestClient(app)

TEST_SECRET_KEY = "test-jwt-secret-key-1234567890-secure-32bytes"


def generate_test_jwt(
    sub: str = "test-user-123",
    email: str = "admin@accessoryinventory.com",
    app_metadata: Optional[Dict[str, Any]] = None,
    user_metadata: Optional[Dict[str, Any]] = None,
    expired: bool = False,
    invalid_claims: bool = False,
) -> str:
    now = datetime.now(timezone.utc)
    exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    payload = {
        "sub": "" if invalid_claims else sub,
        "email": email,
        "role": "authenticated",
        "aud": "authenticated",
        "app_metadata": app_metadata or {},
        "user_metadata": user_metadata or {},
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    secret = settings.SUPABASE_JWT_SECRET or TEST_SECRET_KEY
    return jwt.encode(payload, secret, algorithm="HS256")


def clear_auth_overrides():
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]
    if require_admin in app.dependency_overrides:
        del app.dependency_overrides[require_admin]


def test_health_endpoint_public_without_token():
    """Verify GET /health remains publicly accessible without any authorization headers."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_root_endpoint_public_without_token():
    """Verify GET / remains publicly accessible."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "name" in resp.json()


def test_missing_auth_header_rejected_on_all_endpoints():
    """Verify all protected endpoints reject requests without Authorization header with 401."""
    clear_auth_overrides()

    endpoints = [
        ("GET", "/api/categories"),
        ("POST", "/api/categories"),
        ("GET", "/api/products"),
        ("POST", "/api/products"),
        ("GET", "/api/sales"),
        ("POST", "/api/sales"),
        ("GET", "/api/orders"),
        ("POST", "/api/orders"),
        ("GET", "/api/customers"),
        ("POST", "/api/customers"),
        ("GET", "/api/dashboard/summary"),
        ("GET", "/api/dashboard/revenue"),
        ("POST", "/api/products/PRD-101/image"),
        ("DELETE", "/api/products/PRD-101/image"),
    ]

    for method, endpoint in endpoints:
        if method == "GET":
            resp = client.get(endpoint)
        elif method == "POST":
            resp = client.post(endpoint, json={})
        elif method == "DELETE":
            resp = client.delete(endpoint)

        assert resp.status_code == 401, f"{method} {endpoint} did not return 401 on missing auth: {resp.status_code}"
        assert "detail" in resp.json()


def test_malformed_auth_header_rejected():
    """Verify non-bearer headers return 401."""
    clear_auth_overrides()

    resp = client.get("/api/products", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert resp.status_code == 401
    assert "Bearer" in resp.json()["detail"]


def test_expired_jwt_rejected():
    """Verify expired token returns 401."""
    clear_auth_overrides()

    expired_token = generate_test_jwt(expired=True)
    resp = client.get("/api/products", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


def test_invalid_jwt_format_rejected():
    """Verify garbage/unparseable token returns 401."""
    clear_auth_overrides()

    resp = client.get("/api/products", headers={"Authorization": "Bearer not-a-valid-jwt-token"})
    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"].lower()


def test_valid_non_admin_user_rejected_with_403_on_all_endpoints():
    """
    Verify valid authenticated users without admin privileges receive 403 Forbidden on all administrative endpoints.
    """
    clear_auth_overrides()

    # Valid Supabase token for standard customer/non-admin user
    non_admin_token = generate_test_jwt(
        sub="non-admin-user-456",
        email="customer@example.com",
        app_metadata={"role": "user", "provider": "email"},
        user_metadata={"name": "Customer User"},
    )

    endpoints = [
        ("GET", "/api/categories"),
        ("POST", "/api/categories"),
        ("GET", "/api/products"),
        ("POST", "/api/products"),
        ("GET", "/api/sales"),
        ("POST", "/api/sales"),
        ("GET", "/api/orders"),
        ("POST", "/api/orders"),
        ("GET", "/api/customers"),
        ("POST", "/api/customers"),
        ("GET", "/api/dashboard/summary"),
        ("GET", "/api/dashboard/revenue"),
        ("POST", "/api/products/PRD-101/image"),
        ("DELETE", "/api/products/PRD-101/image"),
    ]

    for method, endpoint in endpoints:
        headers = {"Authorization": f"Bearer {non_admin_token}"}
        if method == "GET":
            resp = client.get(endpoint, headers=headers)
        elif method == "POST":
            resp = client.post(endpoint, json={}, headers=headers)
        elif method == "DELETE":
            resp = client.delete(endpoint, headers=headers)

        assert resp.status_code == 403, f"{method} {endpoint} did not return 403 Forbidden for non-admin: {resp.status_code}"
        assert "administrator" in resp.json()["detail"].lower() or "forbidden" in resp.json()["detail"].lower()


def test_frontend_is_admin_flag_bypass_attempt_rejected():
    """
    Verify that frontend claims, custom headers, or user_metadata cannot bypass server-side authorization.
    """
    clear_auth_overrides()

    # User attempts to spoof admin via user_metadata (user-editable claim)
    spoofed_token = generate_test_jwt(
        sub="attacker-789",
        email="attacker@external.com",
        app_metadata={},  # No server-side admin role
        user_metadata={"role": "admin", "is_admin": True},  # Untrusted client metadata
    )

    headers = {
        "Authorization": f"Bearer {spoofed_token}",
        "X-Is-Admin": "true",
        "X-User-Role": "admin",
    }

    resp = client.get("/api/dashboard/summary", headers=headers)
    assert resp.status_code == 403
    assert "administrator" in resp.json()["detail"].lower() or "forbidden" in resp.json()["detail"].lower()


def test_valid_admin_with_app_metadata_role_authenticates_successfully():
    """Verify valid admin user with app_metadata role='admin' grants access."""
    clear_auth_overrides()

    admin_token = generate_test_jwt(
        sub="admin-super-999",
        email="custom_admin@enterprise.internal",
        app_metadata={"role": "admin"},
    )
    resp = client.get("/api/customers", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_valid_admin_with_allowlist_email_authenticates_successfully():
    """Verify valid admin user on ADMIN_EMAILS allowlist grants access."""
    clear_auth_overrides()

    admin_token = generate_test_jwt(
        sub="admin-allowlist-001",
        email="admin@accessoryinventory.com",
        app_metadata={},
    )
    resp = client.get("/api/customers", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
