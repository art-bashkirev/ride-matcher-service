"""Configuration module using Pydantic BaseSettings."""

from pydantic import Field, validator
from pydantic_settings import BaseSettings
import pytz


class Config(BaseSettings):
    """Application configuration using Pydantic BaseSettings."""
    
    # API Configuration
    yandex_schedules_api_key: str = Field(..., env="YANDEX_SCHEDULES_API_KEY")
    
    # Application Configuration  
    result_timezone: str = Field("Europe/Moscow", env="RESULT_TIMEZONE")
    environment: str = Field("development", env="ENVIRONMENT")
    
    @validator('result_timezone')
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global config instance
_config = None


def get_config() -> Config:
    """Get the application configuration."""
    global _config
    if _config is None:
        _config = Config()
    return _config