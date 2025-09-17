#!/usr/bin/env python3
"""
Simple test script to verify the config module works correctly.
This demonstrates how the config module handles different scenarios.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Helper function to mask sensitive values for safe logging
def mask_secret(secret, visible=3):
    if not isinstance(secret, str):
        secret = str(secret)
    if len(secret) <= visible + 2:
        return '*' * len(secret)
    return secret[:visible] + '*' * (len(secret) - visible - 2) + secret[-2:]

def test_config_with_env_vars():
    """Test config module with environment variables set."""
    print("=== Testing config with environment variables ===")
    
    # Set required environment variable
    os.environ["YANDEX_SCHEDULES_API_KEY"] = "test_api_key_123"
    os.environ["RESULT_TIMEZONE"] = "America/New_York"
    os.environ["ENVIRONMENT"] = "production"
    
    try:
        from config import get_config, reload_config
        
        # Force reload to pick up new env vars
        config = reload_config()
        
        print("✓ API Key: [REDACTED]")
        print(f"✓ Timezone: {config.result_timezone}")
        print(f"✓ Environment: {config.environment}")
        print(f"✓ Is Production: {config.is_production}")
        print(f"✓ Is Development: {config.is_development}")
        print(f"✓ Current Date: {config.get_current_date()}")
        print(f"✓ Timezone Object: {config.timezone}")
        
        assert config.yandex_schedules_api_key == "test_api_key_123"
        assert config.result_timezone == "America/New_York"
        assert config.environment == "production"
        assert config.is_production == True
        assert config.is_development == False
        
        print("✓ All environment variable tests passed!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True


def test_config_missing_api_key():
    """Test config module with missing API key."""
    print("\n=== Testing config with missing API key ===")
    
    # Remove API key
    if "YANDEX_SCHEDULES_API_KEY" in os.environ:
        del os.environ["YANDEX_SCHEDULES_API_KEY"]
    
    try:
        from config import reload_config
        
        # This should raise an error
        config = reload_config()
        print("✗ Should have raised ValueError for missing API key")
        return False
        
    except ValueError as e:
        print(f"✓ Correctly caught error for missing API key: {e}")
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_config_defaults():
    """Test config module with default values."""
    print("\n=== Testing config with defaults ===")
    
    # Set only required API key
    os.environ["YANDEX_SCHEDULES_API_KEY"] = "test_api_key_456"
    
    # Remove optional env vars to test defaults
    for key in ["RESULT_TIMEZONE", "ENVIRONMENT"]:
        if key in os.environ:
            del os.environ[key]
    
    try:
        from config import reload_config
        
        config = reload_config()
        
        print(f"✓ API Key present and loaded correctly.")
        print(f"✓ Default Timezone: {config.result_timezone}")
        print(f"✓ Default Environment: {config.environment}")
        print(f"✓ Is Production: {config.is_production}")
        print(f"✓ Is Development: {config.is_development}")
        
        assert config.yandex_schedules_api_key == "test_api_key_456"
        assert config.result_timezone == "Europe/Moscow"  # default
        assert config.environment == "development"  # default
        assert config.is_production == False
        assert config.is_development == True
        
        print("✓ All default value tests passed!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True


def test_config_invalid_timezone():
    """Test config module with invalid timezone."""
    print("\n=== Testing config with invalid timezone ===")
    
    os.environ["YANDEX_SCHEDULES_API_KEY"] = "test_api_key_789"
    os.environ["RESULT_TIMEZONE"] = "Invalid/Timezone"
    
    try:
        from config import reload_config
        
        # This should raise an error
        config = reload_config()
        print("✗ Should have raised ValueError for invalid timezone")
        return False
        
    except ValueError as e:
        print(f"✓ Correctly caught error for invalid timezone: {e}")
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_legacy_compatibility():
    """Test legacy compatibility functions."""
    print("\n=== Testing legacy compatibility functions ===")
    
    os.environ["YANDEX_SCHEDULES_API_KEY"] = "legacy_test_key"
    os.environ["RESULT_TIMEZONE"] = "Asia/Tokyo"
    
    try:
        from config import get_yandex_api_key, get_result_timezone, get_timezone, reload_config
        
        # Force reload
        reload_config()
        
        api_key = get_yandex_api_key()
        timezone_str = get_result_timezone()
        timezone_obj = get_timezone()
        
        print(f"✓ Legacy API Key: {mask_secret(api_key)}")
        print(f"✓ Legacy Timezone: {timezone_str}")
        print(f"✓ Legacy Timezone Object: {timezone_obj}")
        
        assert api_key == "legacy_test_key"
        assert timezone_str == "Asia/Tokyo"
        assert str(timezone_obj) == "Asia/Tokyo"
        
        print("✓ All legacy compatibility tests passed!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("Starting config module tests...\n")
    
    tests = [
        test_config_with_env_vars,
        test_config_missing_api_key,
        test_config_defaults,
        test_config_invalid_timezone,
        test_legacy_compatibility,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())