import logging
import os
from typing import Optional

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from app.core.config import settings
from app.db.database import get_engine, SessionLocal
from app.db.models import Category, Customer, Order, OrderItem, Product, Sale

TRUTHY = {"1", "true", "yes"}

# Databases with these exact (lowercased) names are shared/system or production
# targets and are always refused, regardless of naming convention.
FORBIDDEN_TEST_DATABASES = {
    "postgres",
    "template0",
    "template1",
    "supabase",
    "db",
    "website_cj",
}

# Structural convention: a test target must be explicitly designated, so its
# database name must end with one of these suffixes.
TEST_DATABASE_SUFFIXES = ("_test", "_ci")


def validate_test_database_target(db_url: Optional[str]) -> str:
    """
    Structural guard against destructive integration-test cleanup aimed at a
    production or shared database. Validates the *parsed* target database name
    (via SQLAlchemy's URL parser — never substring matching across the URL) and
    returns the database name on success. Raises ValueError on rejection.

    Rule: the database name must be present, must not be a reserved/shared
    database, and must be clearly designated for testing (suffix `_test`/`_ci`).

    Limitation: a naming suffix is a convention, not proof of disposability. If
    a real production database was accidentally named e.g. `reporting_test`,
    this guard would not catch it. INTEGRATION_DB_DISPOSABLE=true therefore
    remains the independent human opt-in; both conditions must hold.
    """
    if not db_url or not str(db_url).strip():
        raise ValueError("DATABASE_URL is not configured, so no disposable test target can be identified.")
    try:
        parsed = make_url(str(db_url))
    except ArgumentError as exc:
        raise ValueError(f"DATABASE_URL is not a valid database URL: {exc}") from exc

    database_name = (parsed.database or "").strip().lower()
    if not database_name:
        raise ValueError("DATABASE_URL does not specify a database name.")

    if database_name in FORBIDDEN_TEST_DATABASES:
        raise ValueError(
            f"Refusing integration cleanup against reserved/shared database '{database_name}'."
        )
    if not database_name.endswith(TEST_DATABASE_SUFFIXES):
        raise ValueError(
            f"Integration test database '{database_name}' is not clearly designated for "
            "testing: the database name must end with '_test' or '_ci'. refusing "
            "destructive cleanup against this target."
        )
    return database_name


@pytest.fixture(scope="session")
def db_engine():
    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL environment variable is not configured. Skipping PostgreSQL integration tests.")
    if os.environ.get("INTEGRATION_DB_DISPOSABLE", "").strip().lower() not in TRUTHY:
        pytest.skip(
            "INTEGRATION_DB_DISPOSABLE is not enabled. These tests DELETE all Sales, Products and "
            "Categories in the DATABASE_URL target, so running them requires explicit opt-in: set "
            "INTEGRATION_DB_DISPOSABLE=true only when the database is disposable."
        )
    try:
        validate_test_database_target(settings.DATABASE_URL)
    except ValueError as exc:
        pytest.fail(f"Integration test database target rejected. {exc}")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as exc:
        pytest.skip(f"Could not connect to PostgreSQL database: {exc}")


@pytest.fixture(scope="function")
def db_session(db_engine):
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def clean_remote_db_after_test(db_engine):
    """
    Guarantees clean up of all temporary test data in reverse foreign key order:
    sales -> order_items -> orders -> products -> categories -> customers.
    Ensures the persistent database returns to 0 rows.
    """
    yield
    if db_engine:
        session = SessionLocal()
        try:
            session.query(Sale).delete()
            session.query(OrderItem).delete()
            session.query(Order).delete()
            session.query(Product).delete()
            session.query(Category).delete()
            session.query(Customer).delete()
            session.commit()
        except Exception:
            session.rollback()
            logging.exception("Test data cleanup failed; PostgreSQL test database may be dirty.")
            raise
        finally:
            session.close()
