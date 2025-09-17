"""
Production-ready configuration module for ride-matcher-service.

This module provides a centralized configuration management system that:
- Handles environment variables with proper defaults
- Supports both development and production environments
- Provides type safety and validation
- Is easily testable and mockable
"""

import os
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
import pytz


@dataclass
class Config:
    """Configuration class that holds all application settings."""
    
    # API Configuration
    yandex_schedules_api_key: str
    
    # Application Configuration
    result_timezone: str = "Europe/Moscow"
    environment: str = "development"
    
    # Date configuration
    default_date_format: str = "%Y-%m-%d"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.yandex_schedules_api_key:
            raise ValueError("YANDEX_SCHEDULES_API_KEY is required")
        
        # Validate timezone
        try:
            pytz.timezone(self.result_timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {self.result_timezone}")
    
    @property
    def timezone(self) -> pytz.BaseTzInfo:
        """Get timezone object for the configured timezone."""
        return pytz.timezone(self.result_timezone)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() in ("production", "prod")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ("development", "dev")
    
    def get_current_date(self) -> str:
        """Get current date formatted for API usage."""
        now = datetime.now(self.timezone)
        return now.strftime(self.default_date_format)


class EnvironmentConfig:
    """Environment configuration getter that provides production-ready environment handling."""
    
    def __init__(self, env_prefix: str = ""):
        """
        Initialize environment config.
        
        Args:
            env_prefix: Optional prefix for environment variables (e.g., "RIDE_MATCHER_")
        """
        self.env_prefix = env_prefix
        self._config: Optional[Config] = None
    
    def _get_env_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with optional prefix."""
        full_key = f"{self.env_prefix}{key}" if self.env_prefix else key
        return os.environ.get(full_key, default)
    
    def get_config(self) -> Config:
        """
        Get application configuration from environment variables.
        
        Returns:
            Config: Validated configuration object
            
        Raises:
            ValueError: If required configuration is missing or invalid
        """
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    def _load_config(self) -> Config:
        """Load configuration from environment variables."""
        # Required environment variables
        api_key = self._get_env_var("YANDEX_SCHEDULES_API_KEY")
        if not api_key:
            raise ValueError(
                "YANDEX_SCHEDULES_API_KEY environment variable is required. "
                "Please set it to your Yandex Schedules API key."
            )
        
        # Optional environment variables with defaults
        result_timezone = self._get_env_var("RESULT_TIMEZONE", "Europe/Moscow")
        environment = self._get_env_var("ENVIRONMENT", "development")
        
        return Config(
            yandex_schedules_api_key=api_key,
            result_timezone=result_timezone,
            environment=environment
        )
    
    def reload_config(self) -> Config:
        """Force reload configuration from environment variables."""
        self._config = None
        return self.get_config()


# Global environment config instance
_env_config = EnvironmentConfig()


def get_config() -> Config:
    """
    Get the application configuration.
    
    This is the main function that should be used throughout the application
    to access configuration settings.
    
    Returns:
        Config: Application configuration object
        
    Example:
        >>> from config.settings import get_config
        >>> config = get_config()
        >>> print(config.yandex_schedules_api_key)
        >>> print(config.result_timezone)
        >>> print(config.is_production)
    """
    return _env_config.get_config()


def reload_config() -> Config:
    """
    Reload configuration from environment variables.
    
    Useful for testing or when environment variables change at runtime.
    
    Returns:
        Config: Reloaded configuration object
    """
    return _env_config.reload_config()


# Legacy compatibility functions for existing code
def get_yandex_api_key() -> str:
    """Get Yandex Schedules API key (legacy compatibility)."""
    return get_config().yandex_schedules_api_key


def get_result_timezone() -> str:
    """Get result timezone string (legacy compatibility)."""
    return get_config().result_timezone


def get_timezone() -> pytz.BaseTzInfo:
    """Get timezone object (legacy compatibility)."""
    return get_config().timezone