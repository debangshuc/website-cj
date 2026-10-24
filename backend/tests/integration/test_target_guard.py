import pytest

from tests.integration.conftest import validate_test_database_target


@pytest.fixture(autouse=True)
def clean_remote_db_after_test():
    """Module-local override: these are pure guard validations touching no
    database, so they must run even without INTEGRATION_DB_DISPOSABLE=true
    (which otherwise makes the session db_engine fixture skip every test in
    this package)."""
    yield


@pytest.mark.parametrize(
    "db_url",
    [
        "postgresql+psycopg://localhost:5432/website_cj_test",
        "postgresql://admin:secret-password@db.example.com:5432/website_cj_test",
        "postgresql+psycopg://localhost:5432/ci_runner_01_ci",
    ],
)
def test_guard_accepts_clearly_designated_test_databases(db_url):
    database_name = validate_test_database_target(db_url)
    assert database_name.endswith(("_test", "_ci"))


@pytest.mark.parametrize(
    "db_url",
    [
        "postgresql+psycopg://localhost:5432/website_cj",
        "postgresql+psycopg://localhost:5432/website_cj_prod",
        "postgresql+psycopg://localhost:5432/postgres",
        "postgresql+psycopg://localhost:5432/supabase",
    ],
)
def test_guard_rejects_production_like_database_names(db_url):
    with pytest.raises(ValueError, match="not clearly designated|reserved/shared"):
        validate_test_database_target(db_url)


def test_guard_rejects_missing_configuration():
    with pytest.raises(ValueError, match="not configured"):
        validate_test_database_target("")
    with pytest.raises(ValueError, match="not configured"):
        validate_test_database_target(None)


def test_guard_rejects_url_without_database_name():
    with pytest.raises(ValueError, match="database name"):
        validate_test_database_target("postgresql+psycopg://localhost:5432/")


def test_guard_rejects_malformed_url():
    with pytest.raises(ValueError, match="not a valid database URL"):
        validate_test_database_target("this string is not ::// a ur*l at : aa ll")


def test_guard_rejects_substring_only_match_across_url():
    # 'website_cj_test' appearing in a query parameter must not validate the
    # target; the actual database name is what matters.
    with pytest.raises(ValueError):
        validate_test_database_target(
            "postgresql+psycopg://localhost:5432/website_cj?target=website_cj_test"
        )


def test_guard_does_not_expose_credentials():
    try:
        validate_test_database_target("postgresql://admin:secret-password@db.example.com:5432/website_cj")
    except ValueError as exc:
        assert "secret-password" not in str(exc)
        assert "admin:secret-password" not in str(exc)
    else:
        pytest.fail("guard unexpectedly accepted a production-like database name")


def test_guard_accepts_real_local_test_target(monkeypatch):
    from app.core.config import settings

    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL is not configured on this machine.")
    database_name = validate_test_database_target(settings.DATABASE_URL)
    assert database_name == "website_cj_test"
