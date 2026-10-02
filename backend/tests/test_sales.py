import pytest
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


def test_list_sales():
    response = client.get("/api/sales")
    assert response.status_code == 200
    sales = response.json()
    assert len(sales) == 14
    assert sales[0]["id"] == "SALE-1048"
    assert sales[0]["product_name"] == "Aesthetic Keychain"


def test_get_sale_success():
    response = client.get("/api/sales/SALE-1048")
    assert response.status_code == 200
    sale = response.json()
    assert sale["id"] == "SALE-1048"
    assert sale["product_id"] == "PRD-106"
    assert sale["quantity"] == 2
    assert sale["unit_price"] == "180.00"
    assert sale["total"] == "360.00"


def test_get_sale_not_found():
    response = client.get("/api/sales/SALE-9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_record_valid_sale_and_inventory_sync():
    # 1. Verify before state
    prd_before = client.get("/api/products/PRD-101").json()
    assert prd_before["stock"] == 45
    assert prd_before["units_sold"] == 126

    # 2. Record sale: 2 units of PRD-101 @ 250.00
    payload = {
        "product_id": "PRD-101",
        "quantity": 2,
        "unit_price": "250.00",
    }
    response = client.post("/api/sales", json=payload)
    assert response.status_code == 201
    sale = response.json()
    assert sale["id"].startswith("SALE-")
    assert sale["product_id"] == "PRD-101"
    assert sale["product_name"] == "Anime Poster Collection"
    assert sale["quantity"] == 2
    assert sale["unit_price"] == "250.00"
    assert sale["total"] == "500.00"

    # 3. Verify after state on Product
    prd_after = client.get("/api/products/PRD-101").json()
    assert prd_after["stock"] == 43
    assert prd_after["units_sold"] == 128

    # 4. Verify sale appears in sales listing
    sales_list = client.get("/api/sales").json()
    assert sales_list[0]["id"] == sale["id"]


def test_reject_zero_quantity():
    payload = {
        "product_id": "PRD-101",
        "quantity": 0,
        "unit_price": "250.00",
    }
    response = client.post("/api/sales", json=payload)
    assert response.status_code in [400, 422]


def test_reject_negative_quantity():
    payload = {
        "product_id": "PRD-101",
        "quantity": -5,
        "unit_price": "250.00",
    }
    response = client.post("/api/sales", json=payload)
    assert response.status_code in [400, 422]


def test_reject_quantity_exceeding_stock():
    # PRD-105 stock is 3
    payload = {
        "product_id": "PRD-105",
        "quantity": 10,
        "unit_price": "150.00",
    }
    response = client.post("/api/sales", json=payload)
    assert response.status_code == 400
    assert "Only 3 units are currently available" in response.json()["detail"]


def test_reject_nonexistent_product():
    payload = {
        "product_id": "PRD-9999",
        "quantity": 1,
        "unit_price": "100.00",
    }
    response = client.post("/api/sales", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
