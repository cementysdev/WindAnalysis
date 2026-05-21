"""
Configuration settings for Wind Turbine Analytics API.

Uses pydantic-settings for environment-based configuration with sensible defaults.
"""
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Storage
    volume_path: str = "tmp"  # Default to local, override with VOLUME_PATH env var

    # API metadata
    api_title: str = "Wind Turbine Analytics API"
    api_version: str = "1.0.0"
    api_description: str = "Système d'analyse SCADA pour parcs éoliens"

    # CORS - Allow multiple origins for flexibility
    cors_origins: List[str] = [
        "http://localhost:5173",      # Local dev frontend
        "http://localhost:3000",      # Alternative local port
        "https://*.databricks.com",   # Databricks Apps (wildcard)
        "https://*.azuredatabricks.net",  # Azure Databricks
        "https://*.cloud.databricks.com",  # AWS/GCP Databricks
    ]

    # Authentication (disabled by default, can be enabled later)
    enable_auth: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
