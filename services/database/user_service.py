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
            modules={"models": ["models.user"]}
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
        """Get or create a user."""
        user, created = await User.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
            }
        )
        if not created:
            # Update names if changed
            update_fields = {}
            if username != user.username:
                update_fields["username"] = username
            if first_name != user.first_name:
                update_fields["first_name"] = first_name
            if last_name != user.last_name:
                update_fields["last_name"] = last_name
            if update_fields:
                await user.update_from_dict(update_fields).save()
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
    async def is_user_admin(telegram_id: int) -> bool:
        """Check if user has admin privileges."""
        user = await User.get_or_none(telegram_id=telegram_id)
        return user.is_admin if user else False

    @staticmethod
    async def set_user_admin(telegram_id: int, is_admin: bool) -> Optional[User]:
        """Set user's admin status."""
        user = await User.get_or_none(telegram_id=telegram_id)
        if user:
            user.is_admin = is_admin
            await user.save()
            logger.info("Updated admin status for user %s to %s", telegram_id, is_admin)
        return user