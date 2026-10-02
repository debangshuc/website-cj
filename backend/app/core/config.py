from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Accessory Inventory API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"

    # CORS Origins - configurable via environment variable
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # PostgreSQL Database URL
    DATABASE_URL: Optional[str] = None

    # Supabase Auth / JWT Configuration
    SUPABASE_JWT_SECRET: Optional[str] = None
    SUPABASE_JWT_AUDIENCE: str = "authenticated"

    # Administrator Authorization Allowlist
    ADMIN_EMAILS: List[str] = ["admin@accessoryinventory.com"]

    # Supabase Storage Configuration
    SUPABASE_URL: Optional[str] = "https://odxdlzjneljsviuavqtn.supabase.co"
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_STORAGE_BUCKET: str = "product-images"
    MAX_IMAGE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
