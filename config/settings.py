"""Configuration module using Pydantic BaseSettings (pydantic v2)."""

import pytz
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration using Pydantic BaseSettings.

    Environment variables automatically map from field names in upper/lower case.
    For example: `TELEGRAM_BOT_TOKEN`, `HTTP_PORT`, `LOG_LEVEL`, etc.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra='ignore')

    # API Configuration
    yandex_schedules_api_key: str | None = Field(default=None)
    nvidia_ai_api_key: str | None = Field(default=None)

    # Application Configuration
    result_timezone: str = Field(default="Europe/Moscow")

    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # HTTP server (aiohttp) config
    http_host: str = Field(default="0.0.0.0")
    http_port: int = Field(default=8000)

    # Telegram bot
    telegram_bot_token: str | None = Field(default=None)

    # Redis configuration for caching
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_username: str | None = Field(default=None)
    redis_password: str | None = Field(default=None)

    # Database URIs
    postgresql_uri: str | None = Field(default=None)
    mongodb_host: str | None = Field(default=None)
    mongodb_user: str | None = Field(default=None)
    mongodb_password: str | None = Field(default=None)

    @field_validator('postgresql_uri')
    def fix_postgres_scheme(cls, v):
        """Fix PostgreSQL URI scheme for Tortoise ORM."""
        if v and v.startswith('postgresql://'):
            return v.replace('postgresql://', 'postgres://', 1)
        return v

    # Cache configuration
    cache_ttl_search: int = Field(default=3600)  # 1 hour for search results
    cache_ttl_schedule: int = Field(default=1800)  # 30 minutes for schedule results
    cache_readable_keys: bool = Field(default=False)  # Use readable keys instead of hashes

    @field_validator('result_timezone')
    def validate_timezone(cls, v):
        """Validate timezone string."""
        try:
            pytz.timezone(v)
            return v
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {v}")

    @property
    def timezone(self) -> pytz.BaseTzInfo:
        """Get timezone object."""
        return pytz.timezone(self.result_timezone)

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() in ("production", "prod")

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ("development", "dev")

    @property
    def normalized_log_level(self) -> str:
        """Return an upper-case validated log level string with fallback to INFO."""
        level = str(self.log_level).upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            return "INFO"
        return level

    # (Pydantic v2 replaces inner Config with model_config above.)


# Global config instance
_config = None


def get_config() -> Config:
    """Get the application configuration."""
    global _config
    if _config is None:
        _config = Config()
    return _config
