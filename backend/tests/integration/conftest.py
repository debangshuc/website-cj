import pytest
from sqlalchemy import text
from app.core.config import settings
from app.db.database import get_engine, SessionLocal
from app.db.models import Category, Product, Sale


@pytest.fixture(scope="session")
def db_engine():
    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL environment variable is not configured. Skipping PostgreSQL integration tests.")
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
    sales -> products -> categories.
    Ensures the persistent database returns to 0 rows.
    """
    yield
    if db_engine:
        session = SessionLocal()
        try:
            session.query(Sale).delete()
            session.query(Product).delete()
            session.query(Category).delete()
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
