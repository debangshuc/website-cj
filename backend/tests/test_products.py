import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.product_repository import product_repository

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_repositories():
    product_repository.reset_to_default()
    yield
    product_repository.reset_to_default()


def test_list_products():
    response = client.get("/api/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 12
    assert products[0]["id"] == "PRD-101"
    assert products[0]["name"] == "Anime Poster Collection"


def test_filter_products_by_search():
    response = client.get("/api/products?search=poster")
    assert response.status_code == 200
    products = response.json()
    assert len(products) >= 4
    for p in products:
        assert (
            "poster" in p["name"].lower()
            or "poster" in p["sku"].lower()
            or "poster" in p["category"].lower()
        )


def test_filter_products_by_category():
    response = client.get("/api/products?category=Keychain")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 4
    for p in products:
        assert p["category"] == "Keychain"


def test_filter_products_by_stock_status():
    response = client.get("/api/products?stock_status=low_stock")
    assert response.status_code == 200
    products = response.json()
    for p in products:
        assert 0 < p["stock"] <= 10


def test_get_product_success():
    response = client.get("/api/products/PRD-101")
    assert response.status_code == 200
    product = response.json()
    assert product["id"] == "PRD-101"
    assert product["name"] == "Anime Poster Collection"
    assert product["price"] == "250.00"
    assert product["stock"] == 45
    assert product["units_sold"] == 126


def test_get_product_not_found():
    response = client.get("/api/products/PRD-9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_product():
    payload = {
        "name": "Neon Cyberpunk Poster",
        "sku": "PST-CYB-005",
        "category": "Poster",
        "price": "299.00",
        "stock": 25,
        "description": "Futuristic neon city poster with holographic finish.",
        "image_path": "assets/images/placeholder-poster-main.svg",
    }
    response = client.post("/api/products", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["id"].startswith("PRD-")
    assert created["name"] == "Neon Cyberpunk Poster"
    assert created["price"] == "299.00"
    assert created["stock"] == 25
    assert created["units_sold"] == 0
    assert created["is_active"] is True


def test_update_product():
    payload = {
        "price": "275.00",
        "stock": 50,
    }
    response = client.patch("/api/products/PRD-101", json=payload)
    assert response.status_code == 200
    updated = response.json()
    assert updated["id"] == "PRD-101"
    assert updated["price"] == "275.00"
    assert updated["stock"] == 50
    assert updated["name"] == "Anime Poster Collection"


def test_soft_delete_product():
    # 1. Delete product
    response = client.delete("/api/products/PRD-101")
    assert response.status_code == 204

    # 2. Verify normal product listing excludes it
    list_res = client.get("/api/products")
    assert list_res.status_code == 200
    active_ids = [p["id"] for p in list_res.json()]
    assert "PRD-101" not in active_ids

    # 3. Verify it is included when include_inactive=True
    all_res = client.get("/api/products?include_inactive=true")
    assert all_res.status_code == 200
    all_ids = [p["id"] for p in all_res.json()]
    assert "PRD-101" in all_ids

    # 4. Verify get_by_id still retrieves it with is_active=False
    get_res = client.get("/api/products/PRD-101")
    assert get_res.status_code == 200
    assert get_res.json()["is_active"] is False
