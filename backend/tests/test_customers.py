from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_customers_and_metrics():
    # List all customers
    resp = client.get("/api/customers")
    assert resp.status_code == 200
    customers = resp.json()
    assert isinstance(customers, list)
    assert len(customers) >= 3

    # Metrics
    metrics_resp = client.get("/api/customers/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert "total_customers" in metrics
    assert "active_customers" in metrics
    assert "customers_with_orders" in metrics
    assert "total_revenue" in metrics


def test_get_customer_by_id_and_details_with_orders():
    resp = client.get("/api/customers/cust-001")
    assert resp.status_code == 200
    cust = resp.json()
    assert cust["id"] == "cust-001"
    assert cust["name"] == "Aarav Sharma"
    assert cust["email"] == "aarav.sharma@example.com"
    assert "recent_orders" in cust
    assert isinstance(cust["recent_orders"], list)
    assert cust["completed_order_count"] >= 1
    assert Decimal(str(cust["total_spent"])) >= Decimal("500.00")

    # Nonexistent customer
    resp_404 = client.get("/api/customers/nonexistent-customer-id")
    assert resp_404.status_code == 404


def test_create_customer_success_and_email_normalization():
    payload = {
        "name": "Kavita Nair",
        "email": "  Kavita.Nair@Example.COM  ",
        "phone": "+91 99887 76655",
        "address": "12 Marine Drive, Mumbai",
        "notes": "Prefers WhatsApp notifications",
    }
    resp = client.post("/api/customers", json=payload)
    assert resp.status_code == 201
    cust = resp.json()
    assert cust["name"] == "Kavita Nair"
    # Normalized email
    assert cust["email"] == "kavita.nair@example.com"
    assert cust["is_active"] is True
    assert cust["order_count"] == 0
    assert Decimal(str(cust["total_spent"])) == Decimal("0.00")

    # Duplicate email rejected with 409 Conflict
    dup_resp = client.post("/api/customers", json=payload)
    assert dup_resp.status_code == 409
    assert "already exists" in dup_resp.json()["detail"].lower()


def test_create_customer_validation_errors():
    # Empty name
    resp1 = client.post("/api/customers", json={"name": "   ", "email": "valid@example.com"})
    assert resp1.status_code == 422

    # Invalid email format
    resp2 = client.post("/api/customers", json={"name": "Valid Name", "email": "not-an-email"})
    assert resp2.status_code == 422


def test_update_customer_and_deactivation():
    # 1. Update customer profile
    update_payload = {
        "name": "Kavita N. Menon",
        "phone": "+91 99887 00000",
        "notes": "Updated phone number",
    }
    resp = client.patch("/api/customers/cust-003", json=update_payload)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["name"] == "Kavita N. Menon"
    assert updated["phone"] == "+91 99887 00000"

    # 2. Deactivate customer
    deact_resp = client.patch("/api/customers/cust-003", json={"is_active": False})
    assert deact_resp.status_code == 200
    assert deact_resp.json()["is_active"] is False

    # 3. Filter inactive customers
    inactive_list = client.get("/api/customers?status=inactive").json()
    assert any(c["id"] == "cust-003" for c in inactive_list)

    # 4. Reactivate customer
    react_resp = client.patch("/api/customers/cust-003", json={"is_active": True})
    assert react_resp.status_code == 200
    assert react_resp.json()["is_active"] is True


def test_customer_order_association_and_authoritative_revenue():
    # 1. Create fresh customer
    cust_resp = client.post(
        "/api/customers",
        json={"name": "Siddharth Rao", "email": "sid.rao@example.com"},
    )
    assert cust_resp.status_code == 201
    cust_id = cust_resp.json()["id"]

    # 2. Create pending order for this customer
    order_payload = {
        "customer_id": cust_id,
        "items": [{"product_id": "PRD-101", "quantity": 2}],
    }
    order_resp = client.post("/api/orders", json=order_payload)
    assert order_resp.status_code == 201
    order = order_resp.json()
    order_id = order["id"]
    assert order["customer_id"] == cust_id
    assert order["customer_name"] == "Siddharth Rao"
    assert order["customer_email"] == "sid.rao@example.com"

    # 3. INVARIANT: Pending order is NOT counted towards total_spent
    cust_after_order = client.get(f"/api/customers/{cust_id}").json()
    assert cust_after_order["order_count"] == 1
    assert cust_after_order["completed_order_count"] == 0
    assert Decimal(str(cust_after_order["total_spent"])) == Decimal("0.00")

    # 4. Transition: pending -> confirmed -> completed
    client.patch(f"/api/orders/{order_id}/status", json={"status": "confirmed"})
    complete_resp = client.patch(f"/api/orders/{order_id}/status", json={"status": "completed"})
    assert complete_resp.status_code == 200

    # 5. INVARIANT: Completed order increments total_spent exactly once
    cust_after_complete = client.get(f"/api/customers/{cust_id}").json()
    assert cust_after_complete["completed_order_count"] == 1
    assert Decimal(str(cust_after_complete["total_spent"])) == Decimal("500.00")


def test_historical_integrity_customer_update_preserves_order_snapshots():
    # 1. Create customer
    cust_resp = client.post(
        "/api/customers",
        json={"name": "Alok Verma", "email": "alok.verma@example.com"},
    )
    cust_id = cust_resp.json()["id"]

    # 2. Create order
    order_resp = client.post(
        "/api/orders",
        json={
            "customer_id": cust_id,
            "items": [{"product_id": "PRD-102", "quantity": 1}],
        },
    )
    order_id = order_resp.json()["id"]
    assert order_resp.json()["customer_name"] == "Alok Verma"
    assert order_resp.json()["customer_email"] == "alok.verma@example.com"

    # 3. Update customer name and email
    client.patch(
        f"/api/customers/{cust_id}",
        json={"name": "Alok Kumar Verma", "email": "alok.k.verma@newdomain.com"},
    )

    # 4. CRITICAL INVARIANT: Past order snapshots remain immutable!
    fetched_order = client.get(f"/api/orders/{order_id}").json()
    assert fetched_order["customer_id"] == cust_id
    assert fetched_order["customer_name"] == "Alok Verma"
    assert fetched_order["customer_email"] == "alok.verma@example.com"


def test_cannot_create_order_for_inactive_customer():
    # 1. Create and deactivate customer
    cust_resp = client.post(
        "/api/customers",
        json={"name": "Inactive User", "email": "inactive.user@example.com"},
    )
    cust_id = cust_resp.json()["id"]
    client.patch(f"/api/customers/{cust_id}", json={"is_active": False})

    # 2. Attempting to create order with inactive customer is rejected with 400
    order_resp = client.post(
        "/api/orders",
        json={
            "customer_id": cust_id,
            "items": [{"product_id": "PRD-101", "quantity": 1}],
        },
    )
    assert order_resp.status_code == 400
    assert "inactive" in order_resp.json()["detail"].lower()


def _get_customer_list_entry(client, customer_id):
    listing = client.get("/api/customers", params={"page_size": 100}).json()
    return next(c for c in listing if c["id"] == customer_id)


def test_lifetime_items_aggregate_same_product_and_distinct_products():
    cust_resp = client.post(
        "/api/customers",
        json={"name": "Nisha Roy", "email": "nisha.roy@example.com"},
    )
    assert cust_resp.status_code == 201
    customer_id = cust_resp.json()["id"]

    # Order A: two distinct products, pending (non-cancelled)
    order_a_resp = client.post(
        "/api/orders",
        json={
            "customer_id": customer_id,
            "items": [
                {"product_id": "PRD-101", "quantity": 3},
                {"product_id": "PRD-105", "quantity": 1},
            ],
        },
    )
    assert order_a_resp.status_code == 201
    order_a = order_a_resp.json()

    # Order B: same PRD-101 again (must aggregate) plus another product
    order_b_resp = client.post(
        "/api/orders",
        json={
            "customer_id": customer_id,
            "items": [
                {"product_id": "PRD-101", "quantity": 2},
                {"product_id": "PRD-108", "quantity": 5},
            ],
        },
    )
    assert order_b_resp.status_code == 201
    order_b = order_b_resp.json()

    # 1. Detail exposes the aggregated lifetime breakdown
    detail = client.get(f"/api/customers/{customer_id}").json()
    quantity_by_product = {
        item["product_id"]: item["total_quantity"] for item in detail["lifetime_items"]
    }
    assert quantity_by_product["PRD-101"] == 5  # 3 + 2 across two orders
    assert quantity_by_product["PRD-105"] == 1
    assert quantity_by_product["PRD-108"] == 5
    assert len(detail["lifetime_items"]) == 3  # distinct products, no duplicate rows

    # 2. Existing invariant: non-cancelled count & pending spend semantics unchanged
    assert detail["order_count"] == 2
    assert Decimal(str(detail["total_spent"])) == Decimal("0.00")

    # 3. Listing carries the same breakdown (no N+1 dependency on detail only)
    list_entry = _get_customer_list_entry(client, customer_id)
    list_quantity_by_product = {
        item["product_id"]: item["total_quantity"] for item in list_entry["lifetime_items"]
    }
    assert list_quantity_by_product["PRD-101"] == 5

    # 4. Cancelled orders are excluded from lifetime item quantities
    cancel_b = client.patch(
        f"/api/orders/{order_b['id']}/status", json={"status": "cancelled"}
    )
    assert cancel_b.status_code == 200
    entry_after_cancel = _get_customer_list_entry(client, customer_id)
    after_cancel_quantities = {
        item["product_id"]: item["total_quantity"] for item in entry_after_cancel["lifetime_items"]
    }
    assert after_cancel_quantities == {"PRD-101": 3, "PRD-105": 1}
    assert entry_after_cancel["order_count"] == 1

    cancel_a = client.patch(
        f"/api/orders/{order_a['id']}/status", json={"status": "cancelled"}
    )
    assert cancel_a.status_code == 200
    entry_all_cancelled = _get_customer_list_entry(client, customer_id)
    assert entry_all_cancelled["lifetime_items"] == []
    assert entry_all_cancelled["order_count"] == 0
    assert Decimal(str(entry_all_cancelled["total_spent"])) == Decimal("0.00")


def test_customer_without_orders_has_empty_lifetime_items_summary():
    cust_resp = client.post(
        "/api/customers",
        json={"name": "No Orders Nomad", "email": "nomad@example.com"},
    )
    assert cust_resp.status_code == 201
    customer_id = cust_resp.json()["id"]

    # Customer still appears in listing with an empty summary
    entry = _get_customer_list_entry(client, customer_id)
    assert entry["name"] == "No Orders Nomad"
    assert entry["lifetime_items"] == []
    assert entry["order_count"] == 0
    assert Decimal(str(entry["total_spent"])) == Decimal("0.00")

    detail = client.get(f"/api/customers/{customer_id}").json()
    assert detail["lifetime_items"] == []


def test_seed_customer_lifetime_items_consistent_orders_and_revenue():
    # Seed data: cust-001 has one completed order of PRD-101 quantity 2 (500.00)
    listing = client.get("/api/customers").json()
    aarav = next(c for c in listing if c["id"] == "cust-001")
    assert aarav["lifetime_items"] == [
        {
            "product_id": "PRD-101",
            "product_name": "Anime Poster Collection",
            "total_quantity": 2,
        }
    ]
    assert aarav["order_count"] == 1
    assert aarav["completed_order_count"] == 1
    assert Decimal(str(aarav["total_spent"])) >= Decimal("500.00")

    detail = client.get("/api/customers/cust-001").json()
    assert {i["product_id"]: i["total_quantity"] for i in detail["lifetime_items"]} == {
        "PRD-101": 2
    }
