"""Application configuration using pydantic-settings."""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_secret_key_default() -> str:
    """Get SECRET_KEY with development fallback."""
    key = os.environ.get("SECRET_KEY", "")
    if not key and os.environ.get("ENVIRONMENT", "development") == "development":
        return "dev-only-secret-key-not-for-production"
    return key


def _get_admin_pin_default() -> str:
    """Get ADMIN_PIN with development fallback."""
    pin = os.environ.get("ADMIN_PIN", "")
    if not pin and os.environ.get("ENVIRONMENT", "development") == "development":
        return "0000"
    return pin


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "PhotoBooth"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/photobooth.db"

    # Storage
    storage_path: Path = Path("./data/storage")
    photos_path: Path = Path("./data/storage/photos")
    composites_path: Path = Path("./data/storage/composites")
    thumbnails_path: Path = Path("./data/storage/thumbnails")

    # Printer
    printer_mock_mode: bool = True  # Use mock printer for development
    printer_name: str = "Canon_Selphy_CP1500"
    print_timeout_seconds: int = 120
    max_retry_count: int = 3
    retry_delays: List[int] = [3, 5, 8]  # Seconds between retries

    # Security - REQUIRED in production (set via environment variables)
    secret_key: str = ""
    admin_pin: str = ""
    token_expire_minutes: int = 30

    @field_validator("secret_key", mode="before")
    @classmethod
    def validate_secret_key(cls, v: Optional[str]) -> str:
        """Validate secret_key - required in production."""
        if v:
            return v
        # Allow dev fallback only in development
        env = os.environ.get("ENVIRONMENT", "development")
        if env == "development":
            return "dev-only-secret-key-not-for-production"
        raise ValueError(
            "SECRET_KEY environment variable is required in production. "
            "Generate with: openssl rand -base64 32"
        )

    @field_validator("admin_pin", mode="before")
    @classmethod
    def validate_admin_pin(cls, v: Optional[str]) -> str:
        """Validate admin_pin - required in production."""
        if v:
            return v
        # Allow dev fallback only in development
        env = os.environ.get("ENVIRONMENT", "development")
        if env == "development":
            return "0000"
        raise ValueError(
            "ADMIN_PIN environment variable is required in production. "
            "Set a secure 4-8 digit PIN."
        )

    # Logging
    log_level: str = "INFO"
    log_file: Path = Path("./data/logs/photobooth.log")

    # Session
    session_timeout_minutes: int = 10

    # Image settings
    max_photo_size_bytes: int = 5 * 1024 * 1024  # 5MB
    thumbnail_size: int = 300
    composite_quality: int = 95
    photo_quality: int = 92

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.photos_path.mkdir(parents=True, exist_ok=True)
        self.composites_path.mkdir(parents=True, exist_ok=True)
        self.thumbnails_path.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
