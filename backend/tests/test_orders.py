from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_orders_and_metrics():
    # List all orders
    resp = client.get("/api/orders")
    assert resp.status_code == 200
    orders = resp.json()
    assert isinstance(orders, list)
    assert len(orders) >= 3

    # Filter by status
    pending_resp = client.get("/api/orders?status=pending")
    assert pending_resp.status_code == 200
    pending_orders = pending_resp.json()
    assert all(o["status"] == "pending" for o in pending_orders)

    # Metrics
    metrics_resp = client.get("/api/orders/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert "total_orders" in metrics
    assert "pending_orders" in metrics
    assert "completed_orders" in metrics
    assert "total_revenue" in metrics


def test_get_order_by_id_and_order_number():
    # Lookup by ID
    resp1 = client.get("/api/orders/ord-sample-001")
    assert resp1.status_code == 200
    order1 = resp1.json()
    assert order1["id"] == "ord-sample-001"
    assert order1["order_number"] == "ORD-20260901-A101"
    assert len(order1["items"]) == 1

    # Lookup by order_number
    resp2 = client.get("/api/orders/ORD-20260901-A101")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == "ord-sample-001"

    # Nonexistent
    resp_404 = client.get("/api/orders/nonexistent-order")
    assert resp_404.status_code == 404


def test_create_order_valid_and_stock_reserved():
    # 1. Check initial product stock
    prod_resp = client.get("/api/products/PRD-101")
    assert prod_resp.status_code == 200
    initial_stock = prod_resp.json()["stock"]  # 45

    # 2. Create order for 3 units
    payload = {
        "customer_name": "Vikram Seth",
        "customer_email": "vikram@example.com",
        "notes": "Express delivery requested",
        "items": [
            {
                "product_id": "PRD-101",
                "quantity": 3,
            }
        ],
    }
    resp = client.post("/api/orders", json=payload)
    assert resp.status_code == 201
    order = resp.json()
    assert order["status"] == "pending"
    assert order["customer_name"] == "Vikram Seth"
    assert len(order["items"]) == 1
    item = order["items"][0]
    assert item["quantity"] == 3
    assert Decimal(str(item["unit_price"])) == Decimal("250.00")
    assert Decimal(str(item["line_total"])) == Decimal("750.00")
    assert Decimal(str(order["total"])) == Decimal("750.00")

    # 3. Verify stock was decremented by 3
    after_prod = client.get("/api/products/PRD-101").json()
    assert after_prod["stock"] == initial_stock - 3


def test_create_order_rejections():
    # Nonexistent product
    resp1 = client.post(
        "/api/orders",
        json={"items": [{"product_id": "nonexistent-id", "quantity": 1}]},
    )
    assert resp1.status_code == 404

    # Insufficient stock
    resp2 = client.post(
        "/api/orders",
        json={"items": [{"product_id": "PRD-103", "quantity": 9999}]},
    )
    assert resp2.status_code == 400
    assert "insufficient" in resp2.json()["detail"].lower()

    # Inactive product
    # First soft-delete PRD-103
    client.delete("/api/products/PRD-103")
    resp3 = client.post(
        "/api/orders",
        json={"items": [{"product_id": "PRD-103", "quantity": 1}]},
    )
    assert resp3.status_code == 400
    assert "inactive" in resp3.json()["detail"].lower()


def test_order_lifecycle_and_completion_idempotency():
    # 1. Create order
    payload = {
        "customer_name": "Ananya Roy",
        "customer_email": "ananya@example.com",
        "items": [{"product_id": "PRD-102", "quantity": 2}],
    }
    create_resp = client.post("/api/orders", json=payload)
    assert create_resp.status_code == 201
    order = create_resp.json()
    order_id = order["id"]
    assert order["status"] == "pending"

    # Stock checked
    stock_after_create = client.get("/api/products/PRD-102").json()["stock"]

    # 2. Transition: pending -> confirmed
    confirm_resp = client.patch(f"/api/orders/{order_id}/status", json={"status": "confirmed"})
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "confirmed"

    # Stock remains unchanged
    assert client.get("/api/products/PRD-102").json()["stock"] == stock_after_create

    # 3. Transition: confirmed -> completed
    complete_resp = client.patch(f"/api/orders/{order_id}/status", json={"status": "completed"})
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "completed"

    # CRITICAL INVARIANT: Stock is NOT decremented again upon completion!
    assert client.get("/api/products/PRD-102").json()["stock"] == stock_after_create

    # 4. Verify Sales ledger has the generated sale linked to the order
    sales_resp = client.get("/api/sales")
    assert sales_resp.status_code == 200
    order_sales = [s for s in sales_resp.json() if s.get("order_id") == order_id]
    assert len(order_sales) == 1
    assert Decimal(str(order_sales[0]["total"])) == Decimal("500.00")

    # 5. Idempotent Retry: repeating completion does not duplicate sales
    retry_resp = client.patch(f"/api/orders/{order_id}/status", json={"status": "completed"})
    assert retry_resp.status_code == 200
    sales_after_retry = [s for s in client.get("/api/sales").json() if s.get("order_id") == order_id]
    assert len(sales_after_retry) == 1


def test_order_cancellation_restores_stock():
    # 1. Check initial stock
    initial_stock = client.get("/api/products/PRD-106").json()["stock"]

    # 2. Create order for 4 units
    payload = {
        "customer_name": "Dev Sharma",
        "items": [{"product_id": "PRD-106", "quantity": 4}],
    }
    create_resp = client.post("/api/orders", json=payload)
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]

    # Stock decremented
    assert client.get("/api/products/PRD-106").json()["stock"] == initial_stock - 4

    # 3. Cancel order
    cancel_resp = client.patch(f"/api/orders/{order_id}/status", json={"status": "cancelled"})
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    # 4. INVARIANT: Stock restored exactly once
    assert client.get("/api/products/PRD-106").json()["stock"] == initial_stock

    # 5. Cancelled order cannot be changed
    illegal_resp = client.patch(f"/api/orders/{order_id}/status", json={"status": "confirmed"})
    assert illegal_resp.status_code == 400


def test_invalid_status_transitions_rejected():
    # 1. Create pending order
    create_resp = client.post(
        "/api/orders",
        json={"items": [{"product_id": "PRD-105", "quantity": 1}]},
    )
    order_id = create_resp.json()["id"]

    # Attempt direct jump from pending -> completed (must be confirmed first)
    jump_resp = client.patch(f"/api/orders/{order_id}/status", json={"status": "completed"})
    assert jump_resp.status_code == 400
    assert "invalid status transition" in jump_resp.json()["detail"].lower()


def test_historical_pricing_integrity():
    # 1. Create order for PRD-108 at price ₹120.00
    create_resp = client.post(
        "/api/orders",
        json={"items": [{"product_id": "PRD-108", "quantity": 2}]},
    )
    assert create_resp.status_code == 201
    order = create_resp.json()
    order_id = order["id"]
    assert Decimal(str(order["total"])) == Decimal("240.00")

    # 2. Update product price from ₹120 to ₹350
    update_prod = client.patch("/api/products/PRD-108", json={"price": "350.00"})
    assert update_prod.status_code == 200
    assert Decimal(str(update_prod.json()["price"])) == Decimal("350.00")

    # 3. INVARIANT: Existing order still reflects original ₹120.00 snapshot price
    fetched_order = client.get(f"/api/orders/{order_id}").json()
    assert Decimal(str(fetched_order["items"][0]["unit_price"])) == Decimal("120.00")
    assert Decimal(str(fetched_order["total"])) == Decimal("240.00")
