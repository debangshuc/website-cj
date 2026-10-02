import concurrent.futures
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi import HTTPException
from app.db.database import SessionLocal
from app.repositories.postgres_product_repository import PostgresProductRepository
from app.repositories.postgres_sales_repository import PostgresSalesRepository


def test_postgres_sale_recording_and_atomic_inventory_sync(db_session):
    prod_repo = PostgresProductRepository(db_session)
    sales_repo = PostgresSalesRepository(db_session)

    # 1. Create a product with initial stock 20
    product = prod_repo.create({
        "name": "TEST Keychain Product",
        "sku": f"TEST-KCH-{uuid.uuid4().hex[:6]}",
        "category": "TEST Keychain",
        "price": Decimal("150.00"),
        "stock": 20,
        "units_sold": 5,
    })

    # 2. Record a valid sale of 3 units @ 150.00
    sale = sales_repo.create({
        "product_id": product["id"],
        "quantity": 3,
        "unit_price": Decimal("150.00"),
    })

    assert sale["product_id"] == product["id"]
    assert sale["product_name"] == product["name"]
    assert sale["category"] == "TEST Keychain"
    assert sale["quantity"] == 3
    assert sale["unit_price"] == Decimal("150.00")
    assert sale["total"] == Decimal("450.00")
    assert len(sale["id"]) == 36

    # 3. Verify stock and units_sold on product
    updated_prod = prod_repo.get_by_id(product["id"])
    assert updated_prod["stock"] == 17  # 20 - 3
    assert updated_prod["units_sold"] == 8  # 5 + 3


def test_postgres_sale_rejection_and_rollback(db_session):
    prod_repo = PostgresProductRepository(db_session)
    sales_repo = PostgresSalesRepository(db_session)

    product = prod_repo.create({
        "name": "TEST Low Stock Product",
        "sku": f"TEST-STK-{uuid.uuid4().hex[:6]}",
        "category": "TEST Sticker",
        "price": Decimal("100.00"),
        "stock": 4,
        "units_sold": 10,
    })

    # 1. Zero quantity rejection
    with pytest.raises(HTTPException) as exc_info:
        sales_repo.create({
            "product_id": product["id"],
            "quantity": 0,
            "unit_price": Decimal("100.00"),
        })
    assert exc_info.value.status_code == 400

    # 2. Negative quantity rejection
    with pytest.raises(HTTPException) as exc_info:
        sales_repo.create({
            "product_id": product["id"],
            "quantity": -2,
            "unit_price": Decimal("100.00"),
        })
    assert exc_info.value.status_code == 400

    # 3. Insufficient stock rejection
    with pytest.raises(HTTPException) as exc_info:
        sales_repo.create({
            "product_id": product["id"],
            "quantity": 10,
            "unit_price": Decimal("100.00"),
        })
    assert exc_info.value.status_code == 400
    assert "Only 4 units are currently available." in exc_info.value.detail

    # 4. Verify transaction rollback: stock unchanged and 0 sales recorded
    refreshed_prod = prod_repo.get_by_id(product["id"])
    assert refreshed_prod["stock"] == 4
    assert refreshed_prod["units_sold"] == 10

    all_sales = sales_repo.get_all()
    assert len(all_sales) == 0


def test_postgres_sale_nonexistent_product(db_session):
    sales_repo = PostgresSalesRepository(db_session)

    random_id = str(uuid.uuid4())
    with pytest.raises(HTTPException) as exc_info:
        sales_repo.create({
            "product_id": random_id,
            "quantity": 1,
            "unit_price": Decimal("50.00"),
        })
    assert exc_info.value.status_code == 404


def test_postgres_concurrent_sale_protection_with_row_locking(db_session):
    """
    Verifies that concurrent sale attempts against a product with stock = 1
    are properly serialized by SELECT ... FOR UPDATE row-level locking,
    resulting in exactly 1 successful sale and 1 insufficient-stock rejection.
    """
    prod_repo = PostgresProductRepository(db_session)

    # 1. Create temporary product with stock = 1, units_sold = 0
    product = prod_repo.create({
        "name": "TEST Concurrent Single Unit Product",
        "sku": f"TEST-CNC-{uuid.uuid4().hex[:6]}",
        "category": "TEST Concurrency",
        "price": Decimal("500.00"),
        "stock": 1,
        "units_sold": 0,
    })
    product_id = product["id"]

    def attempt_sale():
        # Independent session & connection per thread
        thread_session = SessionLocal()
        thread_sales_repo = PostgresSalesRepository(thread_session)
        try:
            sale = thread_sales_repo.create({
                "product_id": product_id,
                "quantity": 1,
                "unit_price": Decimal("500.00"),
            })
            return ("SUCCESS", sale)
        except HTTPException as exc:
            return ("ERROR", exc)
        except Exception as exc:
            return ("UNEXPECTED_ERROR", exc)
        finally:
            thread_session.close()

    # 2. Run both transactions concurrently using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(attempt_sale)
        f2 = executor.submit(attempt_sale)
        out1 = f1.result()
        out2 = f2.result()

    outcomes = [out1, out2]
    successes = [item for item in outcomes if item[0] == "SUCCESS"]
    errors = [item for item in outcomes if item[0] == "ERROR"]

    # 3. Exactly 1 must succeed and 1 must fail
    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}: {outcomes}"
    assert len(errors) == 1, f"Expected exactly 1 failure, got {len(errors)}: {outcomes}"

    # 4. Verify failure is 400 Bad Request with insufficient stock message
    fail_exc = errors[0][1]
    assert fail_exc.status_code == 400
    assert "available" in fail_exc.detail.lower()

    # 5. Verify final product state (stock == 0, units_sold == 1)
    db_session.expire_all()
    final_prod = prod_repo.get_by_id(product_id)
    assert final_prod["stock"] == 0
    assert final_prod["units_sold"] == 1

    # 6. Verify exactly 1 sales record exists for this product
    all_sales = [
        s for s in PostgresSalesRepository(db_session).get_all()
        if s["product_id"] == product_id
    ]
    assert len(all_sales) == 1


def test_postgres_daily_revenue_date_trunc_aggregation(db_session):
    prod_repo = PostgresProductRepository(db_session)
    sales_repo = PostgresSalesRepository(db_session)

    # 1. Create product
    prod = prod_repo.create({
        "name": "TEST Historical Aggregation Product",
        "sku": f"TEST-AGG-{uuid.uuid4().hex[:6]}",
        "category": "Poster",
        "price": Decimal("100.00"),
        "stock": 50,
    })
    prod_id = prod["id"]

    now = datetime.now(timezone.utc)
    today_dt = now.replace(hour=12, minute=0, second=0, microsecond=0)
    yesterday_dt = today_dt - timedelta(days=1)
    two_days_ago_dt = today_dt - timedelta(days=2)

    # 2. Record sales at specific days
    sales_repo.create({
        "product_id": prod_id,
        "quantity": 2,
        "unit_price": Decimal("100.00"),
        "sold_at": today_dt.isoformat(),
    })
    sales_repo.create({
        "product_id": prod_id,
        "quantity": 3,
        "unit_price": Decimal("100.00"),
        "sold_at": yesterday_dt.isoformat(),
    })
    sales_repo.create({
        "product_id": prod_id,
        "quantity": 1,
        "unit_price": Decimal("100.00"),
        "sold_at": two_days_ago_dt.isoformat(),
    })

    # 3. Query daily breakdown via PostgreSQL DATE_TRUNC aggregation
    start_date = two_days_ago_dt.replace(hour=0, minute=0, second=0)
    end_date = now
    breakdown = sales_repo.get_daily_revenue_breakdown(start_date, end_date)

    # Filter to our test dates
    date_today_str = today_dt.strftime("%Y-%m-%d")
    date_yesterday_str = yesterday_dt.strftime("%Y-%m-%d")
    date_2days_str = two_days_ago_dt.strftime("%Y-%m-%d")

    day_map = {r["date"]: r for r in breakdown}

    assert date_today_str in day_map
    assert day_map[date_today_str]["revenue"] == Decimal("200.00")
    assert day_map[date_today_str]["order_count"] == 1

    assert date_yesterday_str in day_map
    assert day_map[date_yesterday_str]["revenue"] == Decimal("300.00")
    assert day_map[date_yesterday_str]["order_count"] == 1

    assert date_2days_str in day_map
    assert day_map[date_2days_str]["revenue"] == Decimal("100.00")
    assert day_map[date_2days_str]["order_count"] == 1
