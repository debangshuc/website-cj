from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_category_deactivation_preserves_product_and_historical_sales_integrity():
    """
    Critical Regression Test:
    1. Create Category A ("Custom Plushies")
    2. Create Product under Category A ("Chibi Cat Plush")
    3. Record Sale for Product (2 units @ 450 = 900)
    4. Deactivate Category A
    5. Verify historical Sale still exists with correct category name and total
    6. Verify Dashboard summary and revenue analytics remain intact
    """
    # 1. Create Category A
    cat_resp = client.post(
        "/api/categories",
        json={"name": "Custom Plushies", "description": "Handmade soft plush toys"},
    )
    assert cat_resp.status_code == 201
    category = cat_resp.json()
    cat_id = category["id"]

    # 2. Create Product under Category A
    prod_resp = client.post(
        "/api/products",
        json={
            "name": "Chibi Cat Plush",
            "sku": "PLS-CAT-001",
            "category_id": cat_id,
            "price": "450.00",
            "stock": 20,
            "description": "Fluffy cat plushie",
        },
    )
    assert prod_resp.status_code == 201
    product = prod_resp.json()
    prod_id = product["id"]
    assert product["category"] == "Custom Plushies"

    # 3. Record Sale
    sale_resp = client.post(
        "/api/sales",
        json={
            "product_id": prod_id,
            "quantity": 2,
            "unit_price": "450.00",
        },
    )
    assert sale_resp.status_code == 201
    sale = sale_resp.json()
    sale_id = sale["id"]
    assert Decimal(str(sale["total"])) == Decimal("900.00")
    assert sale["category"] == "Custom Plushies"

    # 4. Deactivate Category A
    del_cat_resp = client.delete(f"/api/categories/{cat_id}")
    assert del_cat_resp.status_code == 204

    # Verify category is now inactive
    get_cat_resp = client.get(f"/api/categories/{cat_id}")
    assert get_cat_resp.status_code == 200
    assert get_cat_resp.json()["is_active"] is False

    # 5. Verify historical Sale still exists and is accessible
    get_sale_resp = client.get(f"/api/sales/{sale_id}")
    assert get_sale_resp.status_code == 200
    fetched_sale = get_sale_resp.json()
    assert fetched_sale["id"] == sale_id
    assert fetched_sale["product_name"] == "Chibi Cat Plush"
    assert Decimal(str(fetched_sale["total"])) == Decimal("900.00")

    # 6. Verify Sales listing includes historical sale
    list_sales_resp = client.get("/api/sales")
    assert list_sales_resp.status_code == 200
    sale_ids = [s["id"] for s in list_sales_resp.json()]
    assert sale_id in sale_ids

    # 7. Verify Dashboard summary metrics reflect the sale
    dash_resp = client.get("/api/dashboard/summary?period=today")
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert Decimal(str(dash_data["today_revenue"])) >= Decimal("900.00")
    assert dash_data["today_sales"] >= 1
