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


@pytest.fixture(autouse=True)
def configured_jwt_secret(monkeypatch):
    """
    All auth tests run with a correctly configured HS256 verification secret
    (the supported signing method). Tests that specifically verify fail-closed
    behavior under missing configuration override this via monkeypatch.
    """
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", TEST_SECRET_KEY)


def generate_test_jwt(
    sub: str = "test-user-123",
    email: str = "admin@accessoryinventory.com",
    app_metadata: Optional[Dict[str, Any]] = None,
    user_metadata: Optional[Dict[str, Any]] = None,
    expired: bool = False,
    invalid_claims: bool = False,
    signing_key: Optional[str] = None,
    audience: Optional[str] = None,
) -> str:
    now = datetime.now(timezone.utc)
    exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    payload = {
        "sub": "" if invalid_claims else sub,
        "email": email,
        "role": "authenticated",
        "aud": audience or settings.SUPABASE_JWT_AUDIENCE,
        "iss": f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1",
        "app_metadata": app_metadata or {},
        "user_metadata": user_metadata or {},
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    secret = signing_key or TEST_SECRET_KEY
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


def test_valid_admin_with_allowlist_email_authenticates_successfully(monkeypatch):
    """Verify valid admin user on ADMIN_EMAILS allowlist grants access."""
    # The test defines its own allowlist so it never depends on the real
    # backend/.env values on this machine or in CI.
    monkeypatch.setattr(settings, "ADMIN_EMAILS", ["allowlist-test-admin@example.com"])
    clear_auth_overrides()

    admin_token = generate_test_jwt(
        sub="admin-allowlist-001",
        email="allowlist-test-admin@example.com",
        app_metadata={},
    )
    resp = client.get("/api/customers", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_missing_jwt_secret_fails_closed(monkeypatch):
    """
    Regression: an empty/missing SUPABASE_JWT_SECRET must disable authentication
    entirely (fail closed). Even a structurally valid, correctly signed token
    must be rejected with 401 rather than accepted without verification.
    """
    clear_auth_overrides()
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", None)

    # Correctly signed, complete token — still rejected without configuration
    valid_token = generate_test_jwt(
        sub="admin-allowlist-001",
        email="admin@accessoryinventory.com",
        app_metadata={},
    )
    resp = client.get("/api/customers", headers={"Authorization": f"Bearer {valid_token}"})
    assert resp.status_code == 401

    # A forged token signed by an attacker is likewise rejected
    forged_token = generate_test_jwt(
        sub="attacker-000",
        email="attacker@external.com",
        app_metadata={"role": "admin"},
        signing_key="attacker-chosen-secret",
    )
    resp = client.get("/api/customers", headers={"Authorization": f"Bearer {forged_token}"})
    assert resp.status_code == 401


def test_forged_token_with_attacker_signature_rejected(monkeypatch):
    """
    Regression: a token signed with a key other than the configured shared
    secret (admin claims included) must be rejected with 401.
    """
    clear_auth_overrides()

    forged_token = generate_test_jwt(
        sub="attacker-000",
        email="attacker@external.com",
        app_metadata={"role": "admin", "is_admin": True},
        signing_key="attacker-chosen-secret",
    )
    resp = client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {forged_token}"})
    assert resp.status_code == 401


def test_wrong_signing_algorithm_rejected(monkeypatch):
    """Tokens signed with a non-HS256 algorithm must be rejected (alg confusion)."""
    clear_auth_overrides()

    now = datetime.now(timezone.utc)
    payload = {
        "sub": "attacker-000",
        "email": "attacker@external.com",
        "app_metadata": {"role": "admin"},
        "aud": settings.SUPABASE_JWT_AUDIENCE,
        "iss": f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    # Sign with a different key but declare HS256; PyJWT's algorithms allowlist
    # must reject any key/verification mismatch.
    weird_token = jwt.encode(payload, b"x" * 32, algorithm="HS256")
    resp = client.get("/api/customers", headers={"Authorization": f"Bearer {weird_token}"})
    assert resp.status_code == 401


def test_wrong_audience_rejected():
    """Tokens with an unexpected audience claim must be rejected with 401."""
    clear_auth_overrides()

    bad_aud_token = generate_test_jwt(
        sub="admin-allowlist-001",
        email="admin@accessoryinventory.com",
        app_metadata={},
        audience="other-service",
    )
    resp = client.get("/api/customers", headers={"Authorization": f"Bearer {bad_aud_token}"})
    assert resp.status_code == 401


def test_foreign_issuer_rejected(monkeypatch):
    """Tokens issued by a different Supabase project must be rejected with 401."""
    clear_auth_overrides()

    other = "https://some-other-project.supabase.co"
    monkeypatch.setattr(settings, "SUPABASE_URL", other)
    foreign_token = generate_test_jwt(
        sub="admin-allowlist-001",
        email="admin@accessoryinventory.com",
        app_metadata={},
    )
    # Token carries attacker-project issuer; verifier expects the configured project.
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://odxdlzjneljsviuavqtn.supabase.co")

    resp = client.get("/api/customers", headers={"Authorization": f"Bearer {foreign_token}"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# ES256 (Supabase JWT signing keys) verification via JWKS
# ---------------------------------------------------------------------------

ES256_TEST_KID = "test-supabase-signing-key"


class _StubSigningKey:
    def __init__(self, key):
        self.key = key


class _StubJWKClient:
    """Deterministic stand-in for PyJWKClient backed by a fixed kid -> key map."""

    def __init__(self, keys_by_kid):
        self._keys_by_kid = keys_by_kid

    def get_signing_key_from_jwt(self, token):
        kid = jwt.get_unverified_header(token).get("kid")
        if kid not in self._keys_by_kid:
            raise jwt.PyJWKClientError(f"Unable to find matching key for kid {kid}")
        return _StubSigningKey(self._keys_by_kid[kid])


def _b64url_uint(value: int) -> str:
    import base64
    padded = value.to_bytes((value.bit_length() + 7) // 8 or 1, "big")
    return base64.urlsafe_b64encode(padded).rstrip(b"=").decode("ascii")


@pytest.fixture(scope="module")
def es256_keypair():
    """Local ES256 keypair + its public JWK (no Supabase/network access)."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    private_key = ec.generate_private_key(ec.SECP256R1())
    numbers = private_key.public_key().public_numbers()
    jwk = {
        "kty": "EC",
        "crv": "P-256",
        "x": _b64url_uint(numbers.x),
        "y": _b64url_uint(numbers.y),
    }
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return {"private_pem": private_pem, "public_jwk": jwk}


def _with_stubbed_jwks(monkeypatch, es256_keypair, kids=(ES256_TEST_KID,)):
    import app.core.security as security_module

    keys_by_kid = {}
    for kid in kids:
        keys_by_kid[kid] = jwt.algorithms.ECAlgorithm.from_jwk(es256_keypair["public_jwk"])
    monkeypatch.setattr(
        security_module,
        "_get_jwk_client",
        lambda: _StubJWKClient(keys_by_kid),
    )


def generate_es256_jwt(
    es256_keypair,
    sub: str = "test-user-123",
    email: str = "user@example.com",
    app_metadata: Optional[Dict[str, Any]] = None,
    user_metadata: Optional[Dict[str, Any]] = None,
    expired: bool = False,
    audience: Optional[str] = None,
    issuer: Optional[str] = None,
    kid: Optional[str] = ES256_TEST_KID,
):
    now = datetime.now(timezone.utc)
    exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    payload = {
        "sub": sub,
        "email": email,
        "role": "authenticated",
        "aud": audience or settings.SUPABASE_JWT_AUDIENCE,
        "iss": issuer or f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1",
        "app_metadata": app_metadata or {},
        "user_metadata": user_metadata or {},
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    headers = {"kid": kid} if kid else {}
    return jwt.encode(payload, es256_keypair["private_pem"], algorithm="ES256", headers=headers)


def test_es256_valid_token_accepted(es256_keypair, monkeypatch):
    """A legitimate ES256 token with matching kid verifies and yields the user."""
    from app.core.security import verify_supabase_jwt

    clear_auth_overrides()
    _with_stubbed_jwks(monkeypatch, es256_keypair)

    token = generate_es256_jwt(es256_keypair, sub="es256-user", email="dev@example.com")
    user = verify_supabase_jwt(token)
    assert user.id == "es256-user"
    assert user.email == "dev@example.com"
    assert user.role == "authenticated"
    assert user.is_admin is False  # plain authenticated users are never auto-admin


def test_es256_admin_via_allowlist_grants_access(es256_keypair, monkeypatch):
    """An ES256-authenticated user listed in ADMIN_EMAILS passes require_admin."""
    clear_auth_overrides()
    _with_stubbed_jwks(monkeypatch, es256_keypair)
    monkeypatch.setattr(settings, "ADMIN_EMAILS", ["hello@accessoryinventory.com"])

    token = generate_es256_jwt(es256_keypair, email="hello@accessoryinventory.com")
    resp = client.get("/api/dashboard/summary?period=week", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_es256_non_admin_rejected_with_403_on_admin_endpoint(es256_keypair, monkeypatch):
    """Valid ES256-authenticated non-admin users must get 403, not 401 or 200."""
    clear_auth_overrides()
    _with_stubbed_jwks(monkeypatch, es256_keypair)
    monkeypatch.setattr(settings, "ADMIN_EMAILS", ["other@accessoryinventory.com"])

    token = generate_es256_jwt(es256_keypair, email="someuser@example.com")
    resp = client.get("/api/dashboard/summary?period=week", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_es256_invalid_signature_rejected(es256_keypair, monkeypatch):
    """ES256 signatures from an untrusted key are rejected with 401."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    clear_auth_overrides()
    _with_stubbed_jwks(monkeypatch, es256_keypair)

    attacker_key = ec.generate_private_key(ec.SECP256R1())
    attacker_pem = attacker_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    forged = jwt.encode(
        {
            "sub": "attacker",
            "email": "attacker@example.com",
            "role": "authenticated",
            "aud": settings.SUPABASE_JWT_AUDIENCE,
            "iss": f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1",
            "app_metadata": {"role": "admin"},
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        },
        attacker_pem,
        algorithm="ES256",
        headers={"kid": ES256_TEST_KID},
    )
    resp = client.get("/api/dashboard/summary?period=week", headers={"Authorization": f"Bearer {forged}"})
    assert resp.status_code == 401


def test_es256_expired_token_rejected(es256_keypair, monkeypatch):
    clear_auth_overrides()
    _with_stubbed_jwks(monkeypatch, es256_keypair)
    token = generate_es256_jwt(es256_keypair, expired=True)
    resp = client.get("/api/dashboard/summary?period=week", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_es256_invalid_issuer_rejected(es256_keypair, monkeypatch):
    clear_auth_overrides()
    _with_stubbed_jwks(monkeypatch, es256_keypair)
    token = generate_es256_jwt(es256_keypair, issuer="https://evil-project.supabase.co/auth/v1")
    resp = client.get("/api/dashboard/summary?period=week", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_es256_invalid_audience_rejected(es256_keypair, monkeypatch):
    clear_auth_overrides()
    _with_stubbed_jwks(monkeypatch, es256_keypair)
    token = generate_es256_jwt(es256_keypair, audience="other-service")
    resp = client.get("/api/dashboard/summary?period=week", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_es256_missing_kid_rejected(es256_keypair, monkeypatch):
    """ES256 tokens without a kid cannot select a trusted signing key -> 401."""
    clear_auth_overrides()
    _with_stubbed_jwks(monkeypatch, es256_keypair)
    token = generate_es256_jwt(es256_keypair, kid=None)
    resp = client.get("/api/dashboard/summary?period=week", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_es256_unknown_kid_rejected(es256_keypair, monkeypatch):
    """kid not present in the project's JWKS must fail closed with 401."""
    clear_auth_overrides()
    _with_stubbed_jwks(monkeypatch, es256_keypair)
    token = generate_es256_jwt(es256_keypair, kid="nope-not-a-real-key")
    resp = client.get("/api/dashboard/summary?period=week", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_es256_jwks_endpoint_failure_rejected(es256_keypair, monkeypatch):
    """A JWKS fetch/network failure must fail closed with 401, never 500."""
    import app.core.security as security_module

    clear_auth_overrides()

    class _ConnectionBrokenJWKClient:
        def get_signing_key_from_jwt(self, token):
            raise jwt.PyJWKClientConnectionError("Fail to fetch data from the url")

    monkeypatch.setattr(security_module, "_get_jwk_client", lambda: _ConnectionBrokenJWKClient())

    token = generate_es256_jwt(es256_keypair)
    resp = client.get("/api/dashboard/summary?period=week", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_none_algorithm_token_rejected(es256_keypair, monkeypatch):
    """A token declaring alg: none with admin claims must be rejected with 401."""
    clear_auth_overrides()
    _with_stubbed_jwks(monkeypatch, es256_keypair)

    now = datetime.now(timezone.utc)
    unsigned = jwt.encode(
        {
            "sub": "attacker-000",
            "email": "attacker@external.com",
            "role": "authenticated",
            "aud": settings.SUPABASE_JWT_AUDIENCE,
            "iss": f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1",
            "app_metadata": {"role": "admin", "is_admin": True},
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        },
        "",
        algorithm="none",
    )
    resp = client.get("/api/dashboard/summary?period=week", headers={"Authorization": f"Bearer {unsigned}"})
    assert resp.status_code == 401


def test_es256_token_without_jwks_configuration_rejected(es256_keypair, monkeypatch):
    """Without SUPABASE_URL or SUPABASE_JWKS_URL there is no trusted key source."""
    from fastapi import HTTPException

    from app.core.security import verify_supabase_jwt

    clear_auth_overrides()
    monkeypatch.setattr(settings, "SUPABASE_URL", None)
    monkeypatch.setattr(settings, "SUPABASE_JWKS_URL", None)
    monkeypatch.setattr("app.core.security._jwk_client", None)
    token = generate_es256_jwt(es256_keypair, issuer="https://odxdlzjneljsviuavqtn.supabase.co/auth/v1")
    with pytest.raises(HTTPException) as exc_info:
        verify_supabase_jwt(token)
    assert exc_info.value.status_code == 401


def test_es256_hs256_secret_not_required_for_es256_tokens(es256_keypair, monkeypatch):
    """With JWT signing keys, ES256 verification works even with no legacy secret."""
    from app.core.security import verify_supabase_jwt

    clear_auth_overrides()
    _with_stubbed_jwks(monkeypatch, es256_keypair)
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", None)
    token = generate_es256_jwt(es256_keypair)
    user = verify_supabase_jwt(token)
    assert user.id == "test-user-123"


def test_hs256_token_rejected_when_legacy_secret_absent(es256_keypair, monkeypatch):
    """HS256 tokens fail closed when SUPABASE_JWT_SECRET is intentionally unset."""
    clear_auth_overrides()
    _with_stubbed_jwks(monkeypatch, es256_keypair)  # ES256 path stays available
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", None)
    hs256_token = generate_test_jwt(sub="legacy-user", email="legacy@example.com")
    resp = client.get("/api/dashboard/summary?period=week", headers={"Authorization": f"Bearer {hs256_token}"})
    assert resp.status_code == 401


def test_es256_token_with_garbage_header_rejected(monkeypatch):
    """Malformed tokens fail closed with 401 rather than 500."""
    clear_auth_overrides()
    resp = client.get(
        "/api/dashboard/summary?period=week",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert resp.status_code == 401
