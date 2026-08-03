"""
core/config.py
==============
Centralised application settings powered by pydantic-settings.

Values are read from environment variables (or a .env file at project root)
with sensible defaults for local development.  Production deployments should
override every default via environment variables – never hard-code secrets.

Architectural note:
  A single Settings singleton (get_settings()) is cached with
  @lru_cache so the .env file is parsed exactly once per process,
  avoiding repeated I/O on every request.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration object."""

    # ------------------------------------------------------------------
    # API metadata
    # ------------------------------------------------------------------
    app_name: str = Field(
        default="Enterprise Decision Intelligence Platform",
        description="Displayed in Swagger UI and OpenAPI spec.",
    )
    app_version: str = Field(default="1.0.0")
    app_description: str = Field(
        default=(
            "Production-grade SaaS backend for AI-powered enterprise analytics. "
            "Provides dataset ingestion, automatic profiling, ML recommendations, "
            "and multi-agent decision intelligence."
        )
    )
    debug: bool = Field(default=False, description="Enable debug mode (never True in prod).")

    # ------------------------------------------------------------------
    # Upload settings
    # ------------------------------------------------------------------
    # Absolute path to the uploads directory.
    # Resolved at startup relative to this file so it works regardless
    # of the working directory the process is launched from.
    upload_dir: Path = Field(
        default=Path(__file__).resolve().parents[3] / "uploads",
        description="Filesystem path where uploaded datasets are persisted.",
    )

    # Maximum accepted file size in megabytes (configurable per environment).
    max_file_size_mb: float = Field(
        default=50.0,
        gt=0,
        description="Upload size ceiling in MB. Requests exceeding this are rejected with 413.",
    )

    # Allowed MIME-type extensions (lower-case, dot-prefixed).
    allowed_extensions: list[str] = Field(
        default=[".csv", ".xlsx"],
        description="Whitelist of accepted file extensions.",
    )

    # ------------------------------------------------------------------
    # Future: Database
    # ------------------------------------------------------------------
    # database_url: str = Field(
    #     default="postgresql+asyncpg://user:pass@localhost:5432/edip",
    #     description="Async SQLAlchemy connection string.",
    # )

    # ------------------------------------------------------------------
    # Future: Auth / Security
    # ------------------------------------------------------------------
    # secret_key: str = Field(..., description="JWT signing secret – MUST be set in prod.")
    # access_token_expire_minutes: int = Field(default=60)

    # ------------------------------------------------------------------
    # pydantic-settings configuration
    # ------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Allow nested env vars like UPLOAD__MAX_FILE_SIZE_MB if needed later.
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached Settings singleton.

    Use this function (not the class directly) everywhere in the application
    so that tests can monkeypatch it via dependency injection without
    reloading the module.

    Example::

        from app.core.config import get_settings
        settings = get_settings()
    """
    return Settings()
