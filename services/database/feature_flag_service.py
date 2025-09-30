"""Feature flag persistence service using Tortoise ORM."""

from typing import Optional

from tortoise.exceptions import IntegrityError

from config.log_setup import get_logger
from models.feature_flag import FeatureFlag

logger = get_logger(__name__)


class FeatureFlagService:
    """CRUD helpers for feature flags."""

    DEFAULT_FLAGS = {
        "ai_mode": False,
    }

    @classmethod
    async def get_flag(cls, key: str) -> Optional[FeatureFlag]:
        """Fetch a feature flag by key."""
        return await FeatureFlag.get_or_none(key=key)

    @classmethod
    async def get_or_create_flag(cls, key: str) -> FeatureFlag:
        """Ensure a flag exists and return it."""
        default_enabled = cls.DEFAULT_FLAGS.get(key, False)
        flag, created = await FeatureFlag.get_or_create(
            key=key,
            defaults={"is_enabled": default_enabled},
        )
        if created:
            logger.info("Feature flag %s created with default state=%s", key, default_enabled)
        return flag

    @classmethod
    async def get_flag_value(cls, key: str, *, default: Optional[bool] = None) -> bool:
        """Get the boolean value for a flag, falling back to defaults."""
        flag = await cls.get_flag(key)
        if flag:
            return flag.is_enabled

        if default is None:
            default = cls.DEFAULT_FLAGS.get(key, False)

        try:
            flag = await FeatureFlag.create(key=key, is_enabled=default)
            logger.info("Feature flag %s missing; created with default state=%s", key, default)
        except IntegrityError:
            # Another coroutine might have created it concurrently; refetch
            flag = await cls.get_flag(key)
            if flag:
                return flag.is_enabled
            logger.error("Feature flag %s could not be created or fetched; returning default=%s", key, default)
            return bool(default)

        return flag.is_enabled

    @classmethod
    async def set_flag_value(cls, key: str, enabled: bool) -> bool:
        """Persist a boolean flag value."""
        flag, _ = await FeatureFlag.update_or_create(
            key=key,
            defaults={"is_enabled": enabled},
        )
        logger.info("Feature flag %s set to %s", key, enabled)
        return flag.is_enabled
