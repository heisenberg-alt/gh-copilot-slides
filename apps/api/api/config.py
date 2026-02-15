"""
Application configuration using Pydantic Settings.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    version: str = "2.0.0"
    debug: bool = False

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_key: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-02-01"

    # Azure Blob Storage
    azure_storage_connection_string: str = ""
    azure_storage_account_name: str = ""
    azure_storage_uploads_container: str = "uploads"
    azure_storage_outputs_container: str = "outputs"
    sas_upload_expiry_hours: int = 1
    sas_download_expiry_hours: int = 24

    # Azure Entra ID
    azure_tenant_id: str = ""
    azure_client_id: str = ""

    # CORS - comma-separated list of origins
    cors_origins: str = "http://localhost:3000,https://localhost:3000"

    @property
    def allowed_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
