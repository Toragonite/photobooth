"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import List, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    printer_name: str = "SelphyCP1500"  # Primary printer (backward compat)
    printer_names: List[str] = []  # Multiple printers; if empty, falls back to printer_name
    printer_selection_strategy: Literal["round-robin", "least-busy", "failover"] = "least-busy"
    print_timeout_seconds: int = 120
    max_retry_count: int = 3
    retry_delays: List[int] = [3, 5, 8]  # Seconds between retries

    @property
    def active_printer_names(self) -> List[str]:
        """Get list of active printer names. Falls back to single printer_name."""
        return self.printer_names if self.printer_names else [self.printer_name]

    # Security
    secret_key: str = "change-me-in-production-very-secret-key"
    admin_pin: str = "1998"  # Default PIN, should be changed
    token_expire_minutes: int = 30

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
