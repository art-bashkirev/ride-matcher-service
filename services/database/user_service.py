"""User database service using Tortoise ORM."""

from typing import Optional

from tortoise import Tortoise

from config.log_setup import get_logger
from config.settings import get_config
from models.user import User

logger = get_logger(__name__)


class UserService:
    """Service for user database operations."""

    @staticmethod
    async def init_db():
        """Initialize Tortoise ORM."""
        config = get_config()
        if not config.postgresql_uri:
            raise ValueError("PostgreSQL URI not configured")

        await Tortoise.init(
            db_url=config.postgresql_uri,
            modules={"models": ["models.user", "models.feature_flag"]}
        )
        # Try to generate schemas, but don't fail if they already exist
        try:
            await Tortoise.generate_schemas(safe=True)
            logger.info("Database schemas generated successfully")
        except Exception as e:
            logger.warning(f"Schema generation failed (this is normal if tables already exist): {e}")
            # Continue anyway - assume tables exist

    @staticmethod
    async def close_db():
        """Close Tortoise ORM connections."""
        await Tortoise.close_connections()

    @staticmethod
    async def get_or_create_user(
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        """Get or create a user. Updates first_name and last_name if they've changed."""
        user, created = await User.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
            }
        )
        
        # Update first_name and last_name if they've changed
        if not created:
            updated = False
            if username is not None and user.username != username:
                user.username = username
                updated = True
            if first_name is not None and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if last_name is not None and user.last_name != last_name:
                user.last_name = last_name
                updated = True
            
            if updated:
                await user.save()
                logger.info("Updated user %s profile information", telegram_id)
        
        return user

    @staticmethod
    async def update_user_stations(
        telegram_id: int,
        base_station_code: str,
        base_station_title: str,
        destination_code: str,
        destination_title: str,
    ) -> User:
        """Update user's station preferences."""
        user = await User.get(telegram_id=telegram_id)
        user.base_station_code = base_station_code
        user.base_station_title = base_station_title
        user.destination_code = destination_code
        user.destination_title = destination_title
        await user.save()
        return user

    @staticmethod
    async def get_user(telegram_id: int) -> Optional[User]:
        """Get user by telegram ID."""
        return await User.get_or_none(telegram_id=telegram_id)

    @staticmethod
    async def set_admin_status(telegram_id: int, is_admin: bool) -> Optional[User]:
        """Set admin status for a user."""
        try:
            user = await User.get(telegram_id=telegram_id)
            user.is_admin = is_admin
            await user.save()
            return user
        except Exception:
            return None