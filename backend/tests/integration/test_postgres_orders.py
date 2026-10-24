import concurrent.futures
import uuid
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.db.database import SessionLocal
from app.db.models import Order, OrderItem, Sale
from app.repositories.postgres_order_repository import PostgresOrderRepository
from app.repositories.postgres_product_repository import PostgresProductRepository
from app.repositories.postgres_sales_repository import PostgresSalesRepository
from app.services.order_service import OrderService


class _CustomerRepoStub:
    """OrderService resolves customer snapshots only when customer_id is provided."""

    def get_by_id(self, customer_id):
        return None


class _OrderItemStub:
    def __init__(self, product_id, quantity):
        self.product_id = product_id
        self.quantity = quantity


class _OrderCreateStub:
    def __init__(self, item_tuples):
        self.items = [_OrderItemStub(pid, qty) for pid, qty in item_tuples]
        self.customer_id = None
        self.customer_name = None
        self.customer_email = None
        self.notes = None


class _OrderStatusUpdateStub:
    def __init__(self, status):
        self.status = status

    def lower(self):
        return self.status


def _order_create(item_tuples):
    return _OrderCreateStub(item_tuples)


def _status_update(status):
    return _OrderStatusUpdateStub(status)


def _new_service(session: SessionLocal) -> OrderService:
    return OrderService(
        order_repo=PostgresOrderRepository(session),
        product_repo=PostgresProductRepository(session),
        sales_repo=PostgresSalesRepository(session),
        customer_repo=_CustomerRepoStub(),
    )


def _new_product(prod_repo: PostgresProductRepository, name: str, stock: int, price: str = "100.00") -> dict:
    return prod_repo.create({
        "name": name,
        "sku": f"TEST-ORD-{uuid.uuid4().hex[:8]}",
        "category": "TEST Order Category",
        "price": Decimal(price),
        "stock": stock,
        "units_sold": 0,
    })


def test_postgres_order_creation_atomic_rollback(db_session, monkeypatch):
    """A failure while creating the order must roll back inventory reservation."""
    prod_repo = PostgresProductRepository(db_session)
    sales_repo = PostgresSalesRepository(db_session)
    service = _new_service(db_session)

    product = _new_product(prod_repo, "TEST Atomic Rollback Product", stock=10)
    product_id = product["id"]

    def failing_create(*args, **kwargs):
        raise RuntimeError("simulated order insert failure")

    monkeypatch.setattr(service.order_repo, "create", failing_create)

    with pytest.raises(HTTPException) as exc_info:
        service.create_order(_order_create([(product_id, 4)]))
    assert exc_info.value.status_code == 500

    reservation = prod_repo.get_by_id(product_id)
    assert reservation["stock"] == 10

    # No order rows were left referencing this product
    product_uuid = uuid.UUID(str(product_id))
    remaining = (
        db_session.query(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(OrderItem.product_id == product_uuid)
        .count()
    )
    assert remaining == 0


def test_postgres_order_lifecycle_sales_and_idempotency(db_session):
    """
    Order lifecycle on Postgres: reservation decrements stock once, completion
    does not decrement again, sale records are created atomically with the
    completed status, units_sold is updated consistently, and repeated
    completion requests do not duplicate sales.
    """
    prod_repo = PostgresProductRepository(db_session)
    order_repo = PostgresOrderRepository(db_session)
    sales_repo = PostgresSalesRepository(db_session)
    service = _new_service(db_session)

    product = _new_product(prod_repo, "TEST Lifecycle Product", stock=8)
    product_id = product["id"]

    created = service.create_order(_order_create([(product_id, 3)]))
    assert created.status == "pending"
    assert Decimal(str(created.total)) == Decimal("300.00")

    refreshed = prod_repo.get_by_id(product_id)
    assert refreshed["stock"] == 5
    assert refreshed["units_sold"] == 0

    order_id = created.id

    confirmed = service.update_order_status(order_id, _status_update("confirmed"))
    assert confirmed.status == "confirmed"

    completed = service.update_order_status(order_id, _status_update("completed"))
    assert completed.status == "completed"

    after = prod_repo.get_by_id(product_id)
    assert after["stock"] == 5
    assert after["units_sold"] == 3

    order_sales = db_session.query(Sale).filter(Sale.order_id == completed.id).all()
    assert len(order_sales) == 1
    assert order_sales[0].quantity == 3
    assert Decimal(str(order_sales[0].total)) == Decimal("300.00")

    retried = service.update_order_status(order_id, _status_update("completed"))
    assert retried.status == "completed"

    sales_after_retry = db_session.query(Sale).filter(Sale.order_id == completed.id).all()
    assert len(sales_after_retry) == 1

    with pytest.raises(HTTPException) as exc_info:
        service.update_order_status(order_id, _status_update("confirmed"))
    assert exc_info.value.status_code == 400


def test_postgres_cancellation_restores_stock_once(db_session):
    """Cancellation restores reserved stock exactly once and stays terminal."""
    prod_repo = PostgresProductRepository(db_session)
    order_repo = PostgresOrderRepository(db_session)
    sales_repo = PostgresSalesRepository(db_session)
    service = _new_service(db_session)

    product = _new_product(prod_repo, "TEST Cancel Product", stock=6)
    product_id = product["id"]
    initial_stock = product["stock"]

    created = service.create_order(_order_create([(product_id, 4)]))
    order_id = created.id
    assert prod_repo.get_by_id(product_id)["stock"] == initial_stock - 4

    service.update_order_status(order_id, _status_update("confirmed"))
    cancelled = service.update_order_status(order_id, _status_update("cancelled"))
    assert cancelled.status == "cancelled"

    assert prod_repo.get_by_id(product_id)["stock"] == initial_stock
    assert (
        db_session.query(Sale).filter(Sale.order_id == cancelled.id).count() == 0
    )

    with pytest.raises(HTTPException) as exc_info:
        service.update_order_status(order_id, _status_update("confirmed"))
    assert exc_info.value.status_code == 400


def test_postgres_concurrent_cancellation_restores_stock_once(db_session):
    """Concurrent duplicate cancellation requests must restore stock exactly once."""
    prod_repo = PostgresProductRepository(db_session)
    order_repo = PostgresOrderRepository(db_session)
    sales_repo = PostgresSalesRepository(db_session)

    product = _new_product(prod_repo, "TEST Cancel Race Product", stock=6)
    product_id = product["id"]
    initial_stock = product["stock"]

    service = _new_service(db_session)
    created = service.create_order(_order_create([(product_id, 4)]))
    order_id = created.id
    service.update_order_status(order_id, _status_update("confirmed"))

    def attempt():
        session = SessionLocal()
        try:
            svc = _new_service(session)
            svc.update_order_status(order_id, _status_update("cancelled"))
            return ("cancelled", None)
        except HTTPException as exc:
            session.rollback()
            return ("failed", exc.status_code)
        finally:
            session.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = [f.result() for f in (executor.submit(attempt), executor.submit(attempt))]

    assert any(o[0] == "cancelled" for o in outcomes)

    final_reader = PostgresProductRepository(SessionLocal())
    assert final_reader.get_by_id(product_id)["stock"] == initial_stock

    persisted = PostgresOrderRepository(SessionLocal()).get_by_id(order_id)
    assert persisted["status"] == "cancelled"


def test_postgres_concurrent_order_creation_cannot_oversell(db_session):
    """Two concurrent orders cannot reserve the same final units of stock."""
    prod_repo = PostgresProductRepository(db_session)
    order_repo = PostgresOrderRepository(db_session)
    sales_repo = PostgresSalesRepository(db_session)

    product = _new_product(prod_repo, "TEST Oversell Product", stock=5)
    product_id = product["id"]

    def attempt():
        session = SessionLocal()
        try:
            svc = _new_service(session)
            svc.create_order(_order_create([(product_id, 4)]))
            return ("created", None)
        except HTTPException as exc:
            session.rollback()
            return ("rejected", exc.status_code)
        finally:
            session.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = [f.result() for f in (executor.submit(attempt), executor.submit(attempt))]

    statuses = sorted(o[0] for o in outcomes)
    assert statuses == ["created", "rejected"]
    assert any(o[1] == 400 for o in outcomes if o[0] == "rejected")

    final = PostgresProductRepository(SessionLocal()).get_by_id(product_id)
    assert final["stock"] == 1


def test_postgres_order_number_collision_retried_with_savepoint(db_session, monkeypatch):
    """A losing order-number candidate is regenerated and retried atomically."""
    prod_repo = PostgresProductRepository(db_session)
    order_repo = PostgresOrderRepository(db_session)
    product = _new_product(prod_repo, "TEST Collision Retry Product", stock=5)

    seed_number = f"ORD-20990101-{uuid.uuid4().hex[:6].upper()}"
    seeded = order_repo.create(
        {"order_number": seed_number, "customer_id": None, "status": "pending"},
        [{"product_id": product["id"], "quantity": 1, "unit_price": Decimal("100.00")}],
    )
    assert seeded["order_number"] == seed_number

    generate_calls = {"count": 0}

    def fake_generate_number():
        generate_calls["count"] += 1
        if generate_calls["count"] == 1:
            return seed_number
        return f"ORD-20990101-{uuid.uuid4().hex[:6].upper()}"

    monkeypatch.setattr(order_repo, "_generate_unique_order_number", fake_generate_number)

    created = order_repo.create(
        {"customer_id": None, "status": "pending"},
        [{"product_id": product["id"], "quantity": 1, "unit_price": Decimal("100.00")}],
    )

    assert generate_calls["count"] >= 2
    assert created["order_number"] != seed_number
    assert db_session.query(Order).filter(Order.order_number == created["order_number"]).count() == 1
    # Both the seeded order and the retried order exist: no partial rows lost.
    assert db_session.query(Order).count() == 2


def test_postgres_order_number_collision_exhausted_raises_and_chain_stays_usable(db_session, monkeypatch):
    """Exhausting retries re-raises the unique violation without leaving the session unusable."""
    prod_repo = PostgresProductRepository(db_session)
    order_repo = PostgresOrderRepository(db_session)
    product = _new_product(prod_repo, "TEST Collision Exhaust Product", stock=5)

    seed_number = f"ORD-20990101-{uuid.uuid4().hex[:6].upper()}"
    order_repo.create(
        {"order_number": seed_number, "customer_id": None, "status": "pending"},
        [{"product_id": product["id"], "quantity": 1, "unit_price": Decimal("100.00")}],
    )

    monkeypatch.setattr(order_repo, "_generate_unique_order_number", lambda: seed_number)

    with pytest.raises(IntegrityError):
        order_repo.create(
            {"customer_id": None, "status": "pending"},
            [{"product_id": product["id"], "quantity": 1, "unit_price": Decimal("100.00")}],
        )

    # Only the seeded order exists; the session remained transactionally usable.
    assert db_session.query(Order).count() == 1
    assert order_repo.get_by_id(seed_number)["order_number"] == seed_number


def test_postgres_concurrent_order_creation_unique_order_numbers(db_session):
    """Concurrently created orders all succeed with distinct order numbers."""
    prod_repo = PostgresProductRepository(db_session)
    product = _new_product(prod_repo, "TEST Concurrent Numbers Product", stock=8)
    product_id = product["id"]

    def attempt():
        session = SessionLocal()
        try:
            svc = _new_service(session)
            created = svc.create_order(_order_create([(product_id, 1)]))
            return ("created", created.order_number)
        except HTTPException as exc:
            session.rollback()
            return ("failed", exc.status_code)
        finally:
            session.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(attempt) for _ in range(4)]
        outcomes = [f.result() for f in futures]

    assert all(outcome[0] == "created" for outcome in outcomes), outcomes
    numbers = [outcome[1] for outcome in outcomes]
    assert len(numbers) == 4
    assert len(set(numbers)) == 4  # no duplicate order numbers

    # No duplicate rows and exactly one order row per number.
    orders = db_session.query(Order).filter(Order.order_number.in_(numbers)).all()
    assert len(orders) == 4
    assert len({o.order_number for o in orders}) == 4

    final_stock = prod_repo.get_by_id(product_id)
    assert final_stock["stock"] == 4  # 8 - 4 successful qty=1 reservations
