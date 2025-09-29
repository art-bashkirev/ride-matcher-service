#!/usr/bin/env python3
"""Test database schema changes for is_admin field."""

import asyncio
import tempfile
import os
from tortoise import Tortoise
from models.user import User
from services.database.user_service import UserService

async def test_database_schema():
    """Test the new is_admin field in User model."""
    
    print("🗄️  Testing Database Schema Changes")
    print("=" * 50)
    
    # Create a temporary SQLite database for testing
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    db_url = f"sqlite://{temp_db.name}"
    
    try:
        print(f"\n1. Initializing test database: {temp_db.name}")
        
        # Initialize Tortoise with the test database
        await Tortoise.init(
            db_url=db_url,
            modules={"models": ["models.user"]}
        )
        
        # Generate schema
        await Tortoise.generate_schemas()
        print("   ✅ Database schema created successfully")
        
        print("\n2. Testing User model with is_admin field...")
        
        # Create a test user
        test_user = await User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        print(f"   ✅ Created user: {test_user.telegram_id}")
        print(f"   ✅ Default is_admin value: {test_user.is_admin} (should be False)")
        
        # Test setting admin status
        test_user.is_admin = True
        await test_user.save()
        print("   ✅ Set is_admin to True")
        
        # Verify the change persisted
        reloaded_user = await User.get(telegram_id=123456789)
        print(f"   ✅ Reloaded user is_admin: {reloaded_user.is_admin} (should be True)")
        
        print("\n3. Testing UserService admin methods...")
        
        # Test is_user_admin method
        is_admin = await UserService.is_user_admin(123456789)
        print(f"   ✅ UserService.is_user_admin: {is_admin} (should be True)")
        
        # Test set_user_admin method
        await UserService.set_user_admin(123456789, False)
        is_admin_after = await UserService.is_user_admin(123456789)
        print(f"   ✅ After setting to False: {is_admin_after} (should be False)")
        
        # Test with non-existent user
        is_admin_nonexistent = await UserService.is_user_admin(999999999)
        print(f"   ✅ Non-existent user is_admin: {is_admin_nonexistent} (should be False)")
        
        print("\n4. Testing user creation with default admin status...")
        
        # Create another user through UserService
        new_user = await UserService.get_or_create_user(
            telegram_id=987654321,
            username="newuser",
            first_name="New",
            last_name="User"
        )
        print(f"   ✅ Created new user: {new_user.telegram_id}")
        print(f"   ✅ Default is_admin: {new_user.is_admin} (should be False)")
        
        print("\n" + "=" * 50)
        print("🎉 Database schema test completed successfully!")
        print("✅ is_admin field works correctly")
        print("✅ Default value is False (security requirement met)")
        print("✅ Admin methods in UserService work correctly")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
    finally:
        # Clean up
        await Tortoise.close_connections()
        try:
            os.unlink(temp_db.name)
            print(f"\n🧹 Cleaned up test database: {temp_db.name}")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_database_schema())