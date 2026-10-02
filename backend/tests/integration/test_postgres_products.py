import uuid
from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError
from app.db.models import Product
from app.repositories.postgres_product_repository import PostgresProductRepository


def test_postgres_product_crud_and_category_resolution(db_session):
    repo = PostgresProductRepository(db_session)

    # 1. Create product with category
    product_data = {
        "name": "TEST Poster Artwork",
        "sku": f"TEST-PST-{uuid.uuid4().hex[:6]}",
        "category": "TEST Category",
        "price": Decimal("299.99"),
        "stock": 25,
        "units_sold": 0,
        "image_path": "assets/images/test.svg",
        "description": "Test product description.",
        "is_active": True,
    }
    created = repo.create(product_data)
    assert created["name"] == product_data["name"]
    assert created["category"] == "TEST Category"
    assert created["price"] == Decimal("299.99")
    assert created["stock"] == 25
    assert created["units_sold"] == 0
    assert created["is_active"] is True
    assert len(created["id"]) == 36

    # 2. Get product by ID
    fetched = repo.get_by_id(created["id"])
    assert fetched is not None
    assert fetched["id"] == created["id"]
    assert fetched["sku"] == product_data["sku"]

    # 3. Update product
    updated = repo.update(
        created["id"],
        {"name": "TEST Poster Artwork Updated", "price": Decimal("349.50")},
    )
    assert updated["name"] == "TEST Poster Artwork Updated"
    assert updated["price"] == Decimal("349.50")

    # 4. Filter products
    all_products = repo.get_all(search="Updated")
    assert len(all_products) == 1
    assert all_products[0]["id"] == created["id"]

    # 5. Soft delete product
    deleted = repo.soft_delete(created["id"])
    assert deleted["is_active"] is False

    # Normal list excludes soft-deleted
    active_products = repo.get_all()
    assert len(active_products) == 0

    # Include inactive includes soft-deleted
    with_inactive = repo.get_all(include_inactive=True)
    assert len(with_inactive) == 1
    assert with_inactive[0]["id"] == created["id"]


def test_postgres_product_image_url_persistence_and_clear(db_session):
    repo = PostgresProductRepository(db_session)
    product_data = {
        "name": "TEST Storage URL Product",
        "sku": f"TEST-IMG-{uuid.uuid4().hex[:6]}",
        "category": "Poster",
        "price": Decimal("150.00"),
        "stock": 10,
        "image_path": None,
    }
    created = repo.create(product_data)
    assert created["image_path"] is None

    # Update with storage URL
    storage_url = f"https://odxdlzjneljsviuavqtn.supabase.co/storage/v1/object/public/product-images/products/{created['id']}/test.png"
    updated = repo.update(created["id"], {"image_path": storage_url})
    assert updated["image_path"] == storage_url

    # Verify fetched from DB
    fetched = repo.get_by_id(created["id"])
    assert fetched["image_path"] == storage_url

    # Clear image
    cleared = repo.update(created["id"], {"image_path": None})
    assert cleared["image_path"] is None


def test_postgres_product_constraints_rejection(db_session):
    repo = PostgresProductRepository(db_session)

    # Creating with negative price should violate CHECK constraint
    cat = repo._get_or_create_category("TEST Constraints")
    invalid_prod = Product(
        name="Invalid Negative Price",
        sku=f"TEST-INV-{uuid.uuid4().hex[:6]}",
        category_id=cat.id,
        price=Decimal("-50.00"),
        stock=10,
    )
    db_session.add(invalid_prod)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
