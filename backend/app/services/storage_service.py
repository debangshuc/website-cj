import mimetypes
from typing import Dict, List, Optional, Protocol, Tuple
import uuid
import httpx
from fastapi import HTTPException, status
from app.core.config import settings


class StorageServiceProtocol(Protocol):
    def validate_image(self, file_bytes: bytes, content_type: str, filename: str) -> None: ...
    def upload_file(self, file_bytes: bytes, filename: str, content_type: str, product_id: str) -> str: ...
    def delete_file(self, image_path_or_url: str) -> bool: ...


def _check_image_magic_bytes(file_bytes: bytes, content_type: str) -> bool:
    """Validate file header magic bytes to prevent spoofed MIME types."""
    if len(file_bytes) < 12:
        return False
    if content_type in ["image/jpeg", "image/jpg"]:
        return file_bytes.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return file_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/webp":
        return file_bytes.startswith(b"RIFF") and file_bytes[8:12] == b"WEBP"
    return False


class BaseStorageService:
    def validate_image(self, file_bytes: bytes, content_type: str, filename: str) -> None:
        # 1. Size Validation
        if len(file_bytes) > settings.MAX_IMAGE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({len(file_bytes)} bytes) exceeds maximum limit of {settings.MAX_IMAGE_SIZE_BYTES} bytes (5 MB)."
            )
        if len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )

        # 2. MIME Type Validation
        normalized_content_type = content_type.lower().split(";")[0].strip()
        if normalized_content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported image type '{content_type}'. Allowed types are JPEG, PNG, WebP."
            )

        # 3. File Extension Validation
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        allowed_extensions = ["jpg", "jpeg", "png", "webp"]
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension '.{ext}'. Allowed extensions are: {', '.join(allowed_extensions)}."
            )

        # 4. Binary Signature / Magic Bytes Validation
        if not _check_image_magic_bytes(file_bytes, normalized_content_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match the specified image format signature."
            )


class InMemoryStorageService(BaseStorageService):
    """In-memory storage service for isolated unit testing and offline development."""
    def __init__(self):
        self._files: Dict[str, Tuple[bytes, str]] = {}

    def upload_file(self, file_bytes: bytes, filename: str, content_type: str, product_id: str) -> str:
        self.validate_image(file_bytes, content_type, filename)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        storage_path = f"products/{product_id}/{unique_name}"
        self._files[storage_path] = (file_bytes, content_type)
        return f"https://mock-storage.supabase.co/storage/v1/object/public/{settings.SUPABASE_STORAGE_BUCKET}/{storage_path}"

    def delete_file(self, image_path_or_url: str) -> bool:
        bucket_prefix = f"/{settings.SUPABASE_STORAGE_BUCKET}/"
        if bucket_prefix in image_path_or_url:
            path = image_path_or_url.split(bucket_prefix, 1)[-1]
        else:
            path = image_path_or_url
        if path in self._files:
            del self._files[path]
            return True
        return False

    def clear(self):
        self._files.clear()


class SupabaseStorageService(BaseStorageService):
    """Production storage service connecting to Supabase Storage REST API."""
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        bucket: Optional[str] = None,
    ):
        self.supabase_url = (supabase_url or settings.SUPABASE_URL or "").rstrip("/")
        self.supabase_key = supabase_key or settings.SUPABASE_KEY or ""
        self.bucket = bucket or settings.SUPABASE_STORAGE_BUCKET

    def _extract_storage_path(self, image_path_or_url: str) -> str:
        bucket_prefix = f"/object/public/{self.bucket}/"
        if bucket_prefix in image_path_or_url:
            return image_path_or_url.split(bucket_prefix, 1)[-1]
        alt_prefix = f"/{self.bucket}/"
        if alt_prefix in image_path_or_url:
            return image_path_or_url.split(alt_prefix, 1)[-1]
        return image_path_or_url

    def upload_file(self, file_bytes: bytes, filename: str, content_type: str, product_id: str) -> str:
        self.validate_image(file_bytes, content_type, filename)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        storage_path = f"products/{product_id}/{unique_name}"

        # If live Supabase credentials are not configured, use fallback mock URL
        if not self.supabase_url or not self.supabase_key:
            return f"https://mock-storage.supabase.co/storage/v1/object/public/{self.bucket}/{storage_path}"

        upload_url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {self.supabase_key}",
            "apikey": self.supabase_key,
            "Content-Type": content_type,
            "x-upsert": "true",
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(upload_url, content=file_bytes, headers=headers)
                if resp.status_code not in [200, 201]:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Supabase storage upload failed: {resp.text}"
                    )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to reach Supabase storage service: {str(exc)}"
            )

        public_url = f"{self.supabase_url}/storage/v1/object/public/{self.bucket}/{storage_path}"
        return public_url

    def delete_file(self, image_path_or_url: str) -> bool:
        if not image_path_or_url:
            return False
        storage_path = self._extract_storage_path(image_path_or_url)
        if not self.supabase_url or not self.supabase_key:
            return True

        delete_url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {self.supabase_key}",
            "apikey": self.supabase_key,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.delete(delete_url, headers=headers)
                return resp.status_code in [200, 204]
        except Exception:
            return False


# Default storage service instance
storage_service = SupabaseStorageService()
