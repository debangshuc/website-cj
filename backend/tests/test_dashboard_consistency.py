import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_product_repository, get_sales_repository
from app.repositories.product_repository import InMemoryProductRepository
from app.repositories.sales_repository import InMemorySalesRepository

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_empty_repositories():
    prod_repo = InMemoryProductRepository()
    prod_repo.clear()
    sales_repo = InMemorySalesRepository()
    sales_repo.clear()
    app.dependency_overrides[get_product_repository] = lambda: prod_repo
    app.dependency_overrides[get_sales_repository] = lambda: sales_repo
    yield
    app.dependency_overrides.clear()


def test_dashboard_consistency_lifecycle_with_soft_delete():
    """
    Comprehensive consistency test verifying metrics across full product & sale lifecycle,
    including active vs soft-deleted product separation.
    """
    # 1. Empty State
    empty_resp = client.get("/api/dashboard/summary")
    assert empty_resp.status_code == 200
    empty_data = empty_resp.json()
    assert empty_data["total_products"] == 0
    assert empty_data["total_stock"] == 0
    assert Decimal(str(empty_data["today_revenue"])) == Decimal("0.00")
    assert empty_data["today_sales"] == 0
    assert empty_data["units_sold_today"] == 0
    assert empty_data["recent_sales"] == []
    assert empty_data["low_stock_products"] == []
    assert Decimal(str(empty_data["revenue_overview"]["total_revenue"])) == Decimal("0.00")

    # 2. Add Active Product (stock = 25, price = 300)
    p_resp = client.post("/api/products", json={
        "name": "Consistency Lifecycle Product",
        "sku": "LIF-001",
        "category": "Poster",
        "price": 300.00,
        "stock": 25
    })
    assert p_resp.status_code == 201
    prod_id = p_resp.json()["id"]

    # Verify dashboard reflects 1 active product
    sum1 = client.get("/api/dashboard/summary").json()
    assert sum1["total_products"] == 1
    assert sum1["total_stock"] == 25
    assert Decimal(str(sum1["today_revenue"])) == Decimal("0.00")
    assert sum1["today_sales"] == 0

    # 3. Record Sale of 4 units @ 300 = 1,200
    s_resp = client.post("/api/sales", json={
        "product_id": prod_id,
        "quantity": 4,
        "unit_price": 300.00
    })
    assert s_resp.status_code == 201

    # Verify inventory decrement & revenue update
    sum2 = client.get("/api/dashboard/summary").json()
    assert sum2["total_products"] == 1
    assert sum2["total_stock"] == 21  # 25 - 4
    assert Decimal(str(sum2["today_revenue"])) == Decimal("1200.00")
    assert sum2["today_sales"] == 1
    assert sum2["units_sold_today"] == 4
    assert len(sum2["recent_sales"]) == 1
    assert sum2["best_selling_product"]["id"] == prod_id
    assert sum2["best_selling_product"]["units_sold"] == 4
    assert Decimal(str(sum2["best_selling_product"]["revenue"])) == Decimal("1200.00")
    assert Decimal(str(sum2["revenue_overview"]["total_revenue"])) == Decimal("1200.00")

    # 4. Soft Delete Product
    del_resp = client.delete(f"/api/products/{prod_id}")
    assert del_resp.status_code == 204

    # Verify: active product count is 0, but historical revenue & sales remain intact
    sum3 = client.get("/api/dashboard/summary").json()
    assert sum3["total_products"] == 0  # Active count is 0
    assert sum3["total_stock"] == 0     # Active stock is 0
    assert Decimal(str(sum3["today_revenue"])) == Decimal("1200.00")  # Historical revenue preserved
    assert sum3["today_sales"] == 1                                  # Historical transaction count preserved
    assert sum3["units_sold_today"] == 4
    assert len(sum3["recent_sales"]) == 1                            # Historical sale still listed
    assert sum3["recent_sales"][0]["product_name"] == "Consistency Lifecycle Product"
    assert Decimal(str(sum3["revenue_overview"]["total_revenue"])) == Decimal("1200.00")
