#!/usr/bin/env python3
"""
Demonstration of the config module usage in different scenarios.
This shows how the config module provides a clean interface for
both development and production environments.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def demo_development_environment():
    """Demonstrate config usage in development environment."""
    print("=" * 60)
    print("DEVELOPMENT ENVIRONMENT DEMO")
    print("=" * 60)
    
    # Set up development environment
    os.environ["YANDEX_SCHEDULES_API_KEY"] = "dev_api_key_12345"
    os.environ["ENVIRONMENT"] = "development"
    # RESULT_TIMEZONE not set - should use default
    
    from config import get_config, reload_config
    
    # Force reload to pick up environment changes
    config = reload_config()
    
    print(f"Environment: {config.environment}")
    print(f"Is Production: {config.is_production}")
    print(f"Is Development: {config.is_development}")
    print(f"API Key is set: {bool(config.yandex_schedules_api_key)}")
    print(f"Timezone: {config.result_timezone}")
    print(f"Current Date: {config.get_current_date()}")
    print(f"Timezone Object: {config.timezone}")
    print()
    
    # Show how this would be used in actual code
    print("Example usage in actual application code:")
    print("```python")
    print("from config import get_config")
    print("from services.yandex_schedules.client import YandexSchedules")
    print("")
    print("config = get_config()")
    print("async with YandexSchedules(config.yandex_schedules_api_key) as client:")
    print("    # Use the client with proper configuration")
    print("    pass")
    print("```")
    print()


def demo_production_environment():
    """Demonstrate config usage in production environment."""
    print("=" * 60)
    print("PRODUCTION ENVIRONMENT DEMO")
    print("=" * 60)
    
    # Set up production environment
    os.environ["YANDEX_SCHEDULES_API_KEY"] = "prod_api_key_xyz789"
    os.environ["ENVIRONMENT"] = "production"
    os.environ["RESULT_TIMEZONE"] = "UTC"
    
    from config import reload_config
    
    # Force reload to pick up environment changes
    config = reload_config()
    
    print(f"Environment: {config.environment}")
    print(f"Is Production: {config.is_production}")
    print(f"Is Development: {config.is_development}")
    print(f"API Key is set: {bool(config.yandex_schedules_api_key)}")
    print(f"Timezone: {config.result_timezone}")
    print(f"Current Date: {config.get_current_date()}")
    print(f"Timezone Object: {config.timezone}")
    print()
    
    # Show production-specific logic
    print("Production-specific configuration logic:")
    print("```python")
    print("config = get_config()")
    print("if config.is_production:")
    print("    # Production-specific settings")
    print("    timeout = 30")
    print("    retry_count = 3")
    print("else:")
    print("    # Development settings")
    print("    timeout = 10")
    print("    retry_count = 1")
    print("```")
    print()


def demo_legacy_compatibility():
    """Demonstrate legacy compatibility functions."""
    print("=" * 60)
    print("LEGACY COMPATIBILITY DEMO")
    print("=" * 60)
    
    # Set up environment for legacy demo
    os.environ["YANDEX_SCHEDULES_API_KEY"] = "legacy_api_key_abc123"
    os.environ["RESULT_TIMEZONE"] = "Asia/Tokyo"
    
    from config import (
        get_yandex_api_key,
        get_result_timezone, 
        get_timezone,
        reload_config
    )
    
    # Force reload
    reload_config()
    
    print("Legacy functions for backward compatibility:")
    print()
    
    # Show legacy usage
    api_key = get_yandex_api_key()
    timezone_str = get_result_timezone()
    timezone_obj = get_timezone()
    
    print(f"API key is set: {bool(api_key)}")
    print(f"get_result_timezone(): {timezone_str}")
    print(f"get_timezone(): {timezone_obj}")
    print()
    
    print("These functions allow existing code to work without changes:")
    print("```python")
    print("# Old way (still supported)")
    print("from config import get_yandex_api_key, get_result_timezone")
    print("")
    print("api_key = get_yandex_api_key()")
    print("timezone = get_result_timezone()")
    print("```")
    print()


def demo_error_handling():
    """Demonstrate error handling for missing configuration."""
    print("=" * 60)
    print("ERROR HANDLING DEMO")
    print("=" * 60)
    
    # Remove required API key
    if "YANDEX_SCHEDULES_API_KEY" in os.environ:
        del os.environ["YANDEX_SCHEDULES_API_KEY"]
    
    from config import reload_config
    
    try:
        config = reload_config()
        print("ERROR: Should have raised an exception!")
    except ValueError as e:
        print("✓ Properly caught configuration error:")
        print(f"  {e}")
        print()
        print("This provides clear guidance to developers about missing configuration.")
    
    print()


def demo_main_py_integration():
    """Show how main.py now uses the config module."""
    print("=" * 60)
    print("MAIN.PY INTEGRATION DEMO")
    print("=" * 60)
    
    # Set up environment for main.py demo
    os.environ["YANDEX_SCHEDULES_API_KEY"] = "main_demo_key_456"
    os.environ["ENVIRONMENT"] = "development"
    os.environ["RESULT_TIMEZONE"] = "Europe/Berlin"
    
    from config import reload_config
    config = reload_config()
    
    print("Before the refactor, main.py had:")
    print("```python")
    print("import os")
    print("YANDEX_SCHEDULES_API_KEY = os.environ.get('YANDEX_SCHEDULES_API_KEY')")
    print("RESULT_TIMEZONE = os.environ.get('RESULT_TIMEZONE', 'Europe/Moscow')")
    print("```")
    print()
    
    print("After the refactor, main.py now has:")
    print("```python")
    print("from config import get_config")
    print("")
    print("config = get_config()")
    print("# Configuration is now validated and type-safe")
    print("```")
    print()
    
    print("Benefits of the new approach:")
    print("• Centralized configuration management")
    print("• Type safety and validation")
    print("• Clear error messages for missing configuration")
    print("• Support for different environments")
    print("• Easy testing and mocking")
    print("• Backward compatibility")
    print()


def main():
    """Run all demonstrations."""
    print("RIDE MATCHER SERVICE - CONFIG MODULE DEMONSTRATION")
    print("This demonstrates the production-ready configuration system")
    print("that replaces direct environment variable access.\n")
    
    demo_development_environment()
    demo_production_environment()
    demo_legacy_compatibility()
    demo_error_handling()
    demo_main_py_integration()
    
    print("=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("The config module provides a clean, type-safe, and production-ready")
    print("way to manage environment variables with proper validation and")
    print("backward compatibility.")


if __name__ == "__main__":
    main()