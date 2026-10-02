import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.product_repository import product_repository
from app.repositories.sales_repository import sales_repository

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_repositories():
    product_repository.reset_to_default()
    sales_repository.reset_to_default()
    yield
    product_repository.reset_to_default()
    sales_repository.reset_to_default()


def test_dashboard_summary():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()

    assert "total_products" in data
    assert data["total_products"] == 12

    assert "total_stock" in data
    assert data["total_stock"] == 169

    assert "today_revenue" in data
    assert Decimal(str(data["today_revenue"])) == Decimal("1670.00")

    assert "today_sales" in data
    assert data["today_sales"] == 5

    assert "units_sold_today" in data
    assert data["units_sold_today"] == 9

    assert "best_selling_product" in data
    assert data["best_selling_product"]["name"] == "Cute Stickers Pack"
    assert data["best_selling_product"]["units_sold"] == 180

    assert "recent_sales" in data
    assert len(data["recent_sales"]) == 5

    assert "low_stock_products" in data
    assert len(data["low_stock_products"]) <= 4

    assert "revenue_overview" in data
    assert data["revenue_overview"] is not None
    assert len(data["revenue_overview"]["points"]) == 7


def test_dashboard_revenue_endpoint_periods():
    # 1. Week period (default)
    resp_week = client.get("/api/dashboard/revenue?period=week")
    assert resp_week.status_code == 200
    data_week = resp_week.json()
    assert data_week["period"] == "week"
    assert len(data_week["points"]) == 7

    # 2. Today period
    resp_today = client.get("/api/dashboard/revenue?period=today")
    assert resp_today.status_code == 200
    data_today = resp_today.json()
    assert data_today["period"] == "today"
    assert len(data_today["points"]) == 1

    # 3. Month period
    resp_month = client.get("/api/dashboard/revenue?period=month")
    assert resp_month.status_code == 200
    data_month = resp_month.json()
    assert data_month["period"] == "month"
    assert len(data_month["points"]) == 30


def test_revenue_analytics_daily_grouping_accuracy():
    # Create test product
    p_resp = client.post("/api/products", json={
        "name": "Analytics Product",
        "sku": "ANL-001",
        "category": "Poster",
        "price": 500.00,
        "stock": 100
    })
    prod_id = p_resp.json()["id"]

    now = datetime.now(timezone.utc)
    two_days_ago = (now - timedelta(days=2)).isoformat()
    three_days_ago = (now - timedelta(days=3)).isoformat()

    # Record sales at past timestamps
    client.post("/api/sales", json={
        "product_id": prod_id,
        "quantity": 2,
        "unit_price": 500.00,
        "sold_at": two_days_ago
    })
    client.post("/api/sales", json={
        "product_id": prod_id,
        "quantity": 1,
        "unit_price": 500.00,
        "sold_at": three_days_ago
    })

    # Fetch week revenue
    resp = client.get("/api/dashboard/revenue?period=week")
    assert resp.status_code == 200
    points = resp.json()["points"]
    assert len(points) == 7

    two_days_ago_date = (now - timedelta(days=2)).strftime("%Y-%m-%d")
    pt_2days = next((p for p in points if p["date"] == two_days_ago_date), None)
    assert pt_2days is not None
    assert Decimal(str(pt_2days["revenue"])) >= Decimal("1000.00")


def test_best_seller_revenue_historical_accuracy_after_price_change():
    """
    Verify that best-selling product revenue is calculated from actual historical sales totals,
    rather than multiplying units_sold by the updated/current product price.
    """
    # 1. Create a product priced at 100.00 with 500 stock
    create_resp = client.post("/api/products", json={
        "name": "Historical Best Seller Test",
        "sku": "TST-REV-001",
        "category": "Poster",
        "price": 100.00,
        "stock": 500
    })
    assert create_resp.status_code == 201
    prod_id = create_resp.json()["id"]

    # 2. Record large sale: 200 units @ 100.00 = 20,000.00 (making it the top best seller)
    sale_resp = client.post("/api/sales", json={
        "product_id": prod_id,
        "quantity": 200,
        "unit_price": 100.00
    })
    assert sale_resp.status_code == 201
    assert Decimal(str(sale_resp.json()["total"])) == Decimal("20000.00")

    # 3. Later, product price increases significantly to 500.00
    patch_resp = client.patch(f"/api/products/{prod_id}", json={
        "price": 500.00
    })
    assert patch_resp.status_code == 200
    assert Decimal(str(patch_resp.json()["price"])) == Decimal("500.00")

    # 4. Check dashboard summary
    dash_resp = client.get("/api/dashboard/summary")
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()

    best_seller = dash_data["best_selling_product"]
    assert best_seller["id"] == prod_id
    assert best_seller["units_sold"] == 200
    assert Decimal(str(best_seller["price"])) == Decimal("500.00")
    # Authoritative historical revenue must be 20000.00 (NOT 200 * 500 = 100000.00)
    assert Decimal(str(best_seller["revenue"])) == Decimal("20000.00")
