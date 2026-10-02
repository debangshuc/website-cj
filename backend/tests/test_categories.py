from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_categories_default_active_only():
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    assert all(c["is_active"] is True for c in data)
    names = [c["name"] for c in data]
    assert "Poster" in names
    assert "Keychain" in names


def test_get_category_by_id_success():
    resp = client.get("/api/categories/cat-poster-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "cat-poster-001"
    assert data["name"] == "Poster"
    assert data["is_active"] is True


def test_get_category_by_id_not_found():
    resp = client.get("/api/categories/nonexistent-category-id")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_create_category_success():
    payload = {
        "name": "Badge & Pins",
        "description": "Collectible metal pins and enamel badges",
    }
    resp = client.post("/api/categories", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Badge & Pins"
    assert data["description"] == "Collectible metal pins and enamel badges"
    assert data["is_active"] is True
    assert "id" in data


def test_create_duplicate_category_rejected_409():
    payload = {"name": "Poster"}  # Poster already exists
    resp = client.post("/api/categories", json=payload)
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"].lower()


def test_create_category_empty_or_whitespace_name_rejected_422():
    resp1 = client.post("/api/categories", json={"name": ""})
    assert resp1.status_code == 422

    resp2 = client.post("/api/categories", json={"name": "   "})
    assert resp2.status_code == 422


def test_update_category_name_and_description():
    payload = {
        "name": "Art Posters & Wall Decals",
        "description": "Updated poster description",
    }
    resp = client.patch("/api/categories/cat-poster-001", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Art Posters & Wall Decals"
    assert data["description"] == "Updated poster description"


def test_update_duplicate_category_name_rejected_409():
    # Attempt to rename Keychain to Poster (which already exists)
    resp = client.patch("/api/categories/cat-keychain-002", json={"name": "Poster"})
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"].lower()


def test_deactivate_and_reactivate_category():
    # 1. Deactivate via DELETE
    resp = client.delete("/api/categories/cat-sticker-003")
    assert resp.status_code == 204

    # 2. Verify excluded by default
    active_resp = client.get("/api/categories")
    active_ids = [c["id"] for c in active_resp.json()]
    assert "cat-sticker-003" not in active_ids

    # 3. Verify included when include_inactive=True
    all_resp = client.get("/api/categories?include_inactive=true")
    inactive_cats = [c for c in all_resp.json() if c["id"] == "cat-sticker-003"]
    assert len(inactive_cats) == 1
    assert inactive_cats[0]["is_active"] is False

    # 4. Reactivate via PATCH
    reactivate_resp = client.patch(
        "/api/categories/cat-sticker-003", json={"is_active": True}
    )
    assert reactivate_resp.status_code == 200
    assert reactivate_resp.json()["is_active"] is True
