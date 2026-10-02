import io
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Minimal valid binary headers for test images
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
VALID_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\xff\xd9"
VALID_WEBP_BYTES = b"RIFF\x1a\x00\x00\x00WEBPVP8 \x0e\x00\x00\x000\x01\x00\x9d\x01*\x01\x00\x01\x00\x00"


@pytest.fixture
def test_product_id():
    resp = client.post("/api/products", json={
        "name": "Storage Test Product",
        "sku": "STRG-001",
        "category": "Poster",
        "price": 250.00,
        "stock": 20,
        "description": "Product for storage unit tests"
    })
    assert resp.status_code == 201
    return resp.json()["id"]


def test_upload_valid_png_image(test_product_id):
    files = {"file": ("test_poster.png", io.BytesIO(VALID_PNG_BYTES), "image/png")}
    response = client.post(f"/api/products/{test_product_id}/image", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["image_path"] is not None
    assert "products/" in data["image_path"]
    assert data["image_path"].endswith(".png")


def test_upload_valid_jpeg_image(test_product_id):
    files = {"file": ("test_photo.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")}
    response = client.post(f"/api/products/{test_product_id}/image", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["image_path"] is not None
    assert data["image_path"].endswith(".jpg")


def test_upload_valid_webp_image(test_product_id):
    files = {"file": ("test_art.webp", io.BytesIO(VALID_WEBP_BYTES), "image/webp")}
    response = client.post(f"/api/products/{test_product_id}/image", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["image_path"] is not None
    assert data["image_path"].endswith(".webp")


def test_reject_unsupported_mime_type(test_product_id):
    fake_txt = b"This is a text file, not an image."
    files = {"file": ("malicious.txt", io.BytesIO(fake_txt), "text/plain")}
    response = client.post(f"/api/products/{test_product_id}/image", files=files)
    assert response.status_code == 400
    assert "Unsupported image type" in response.json()["detail"]


def test_reject_spoofed_magic_bytes(test_product_id):
    spoofed_bytes = b"NOT AN IMAGE DATA BUT CLAIMING TO BE PNG"
    files = {"file": ("spoof.png", io.BytesIO(spoofed_bytes), "image/png")}
    response = client.post(f"/api/products/{test_product_id}/image", files=files)
    assert response.status_code == 400
    assert "signature" in response.json()["detail"]


def test_reject_oversized_file(test_product_id):
    # Create 6 MB dummy payload
    oversized = VALID_PNG_BYTES + (b"\x00" * (6 * 1024 * 1024))
    files = {"file": ("huge.png", io.BytesIO(oversized), "image/png")}
    response = client.post(f"/api/products/{test_product_id}/image", files=files)
    assert response.status_code == 400
    assert "exceeds maximum limit" in response.json()["detail"]


def test_image_replacement_and_delete(test_product_id):
    # 1. Upload initial PNG
    files1 = {"file": ("image1.png", io.BytesIO(VALID_PNG_BYTES), "image/png")}
    resp1 = client.post(f"/api/products/{test_product_id}/image", files=files1)
    assert resp1.status_code == 200
    first_url = resp1.json()["image_path"]

    # 2. Replace with JPEG
    files2 = {"file": ("image2.jpg", io.BytesIO(VALID_JPEG_BYTES), "image/jpeg")}
    resp2 = client.post(f"/api/products/{test_product_id}/image", files=files2)
    assert resp2.status_code == 200
    second_url = resp2.json()["image_path"]
    assert second_url != first_url

    # 3. Delete image
    del_resp = client.delete(f"/api/products/{test_product_id}/image")
    assert del_resp.status_code == 200
    assert del_resp.json()["image_path"] is None


def test_soft_delete_preserves_image_path(test_product_id):
    files = {"file": ("preserved.png", io.BytesIO(VALID_PNG_BYTES), "image/png")}
    upload_resp = client.post(f"/api/products/{test_product_id}/image", files=files)
    assert upload_resp.status_code == 200
    image_url = upload_resp.json()["image_path"]

    # Soft delete
    del_resp = client.delete(f"/api/products/{test_product_id}")
    assert del_resp.status_code == 204

    # Fetch product and verify image_path is intact
    get_resp = client.get(f"/api/products/{test_product_id}")
    assert get_resp.status_code == 200
    prod = get_resp.json()
    assert prod["is_active"] is False
    assert prod["image_path"] == image_url
