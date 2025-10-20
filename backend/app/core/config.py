"""
Application Configuration

Centralized configuration management using Pydantic Settings.
All environment variables are loaded, validated, and typed here.

This ensures:
- Type safety for all config values
- Single source of truth for configuration
- Automatic validation on startup
- Clear documentation of required/optional env vars
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables are loaded from:
    1. Environment variables
    2. .env file (if present)

    All settings have sensible defaults where appropriate.
    """

    # ========================================================================
    # Application Settings
    # ========================================================================

    environment: str = "development"
    """Environment: development, staging, or production"""

    log_level: str = "INFO"
    """Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"""

    api_host: str = "0.0.0.0"
    """API server host"""

    api_port: int = 8000
    """API server port"""

    # ========================================================================
    # LLM Provider Settings
    # ========================================================================

    openai_api_key: str
    """OpenAI API key (required) - also works with OpenAI-compatible APIs"""

    openai_base_url: Optional[str] = None
    """
    Base URL for OpenAI-compatible API.
    Examples:
    - None (uses official OpenAI)
    - https://router.huggingface.co/v1
    - https://albert.api.etalab.gouv.fr/v1
    - http://localhost:11434/v1 (Ollama)
    """

    openai_model: str = "gpt-4o-mini"
    """
    Model to use for LLM calls.
    Examples:
    - gpt-4o-mini (OpenAI)
    - gpt-4o (OpenAI)
    - openai/gpt-oss-120b (HuggingFace)
    - albert-large (Etalab)
    """

    llm_temperature: float = 0.0
    """LLM temperature (0.0 = deterministic, 2.0 = very creative)"""

    llm_max_tokens: Optional[int] = None
    """Maximum tokens in LLM response (None = model default)"""

    llm_timeout: int = 60
    """Timeout for LLM requests in seconds"""

    llm_max_retries: int = 2
    """Maximum number of retries for failed LLM requests"""

    # ========================================================================
    # Grist Settings
    # ========================================================================

    grist_base_url: str = "https://docs.getgrist.com"
    """
    Base URL for Grist instance.
    Examples:
    - https://docs.getgrist.com (official)
    - https://grist.numerique.gouv.fr (DINUM)
    - https://your-grist.example.com (self-hosted)
    """

    # ========================================================================
    # Database Settings (for future use)
    # ========================================================================

    database_url: Optional[str] = None
    """PostgreSQL database URL (optional, for conversation history)"""

    # ========================================================================
    # Redis Settings (for future use)
    # ========================================================================

    redis_url: Optional[str] = None
    """Redis URL (optional, for caching and rate limiting)"""

    # ========================================================================
    # Agent Settings
    # ========================================================================

    agent_max_iterations: int = 15
    """Maximum number of tool calls the agent can make"""

    agent_verbose: bool = True
    """Whether to log agent actions"""

    # ========================================================================
    # Security Settings (for production)
    # ========================================================================

    api_key: Optional[str] = None
    """API key for authentication (optional)"""

    jwt_secret: Optional[str] = None
    """JWT secret for token signing (optional)"""

    cors_origins: list[str] = ["*"]
    """CORS allowed origins (use specific origins in production)"""

    # ========================================================================
    # Pydantic Settings Configuration
    # ========================================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # Environment variables are case-insensitive
        extra="ignore",  # Ignore extra environment variables
    )


# ============================================================================
# Global Settings Instance
# ============================================================================

settings = Settings()
"""
Global settings instance.

Usage:
    from app.models import settings

    print(settings.openai_model)
    print(settings.grist_base_url)
"""


# ============================================================================
# Helper Functions
# ============================================================================


def get_settings() -> Settings:
    """
    Get the global settings instance.

    Useful for dependency injection in FastAPI:
        from fastapi import Depends
        from app.models import get_settings, Settings

        @app.get("/")
        def read_root(settings: Settings = Depends(get_settings)):
            return {"model": settings.openai_model}
    """
    return settings


def is_development() -> bool:
    """Check if running in development environment."""
    return settings.environment.lower() == "development"


def is_production() -> bool:
    """Check if running in production environment."""
    return settings.environment.lower() == "production"
