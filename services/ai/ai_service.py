"""AI chat bot service integration."""

from typing import Optional

from config.log_setup import get_logger
from services.ai.client import NvidiaAIClient
from services.cache.ai_flag_service import AIChatBotFlagService
from services.database.user_service import UserService

logger = get_logger(__name__)


class AIChatBotService:
    """Service for handling AI chat bot interactions."""

    def __init__(self):
        """Initialize the AI chat bot service."""
        self.flag_service = AIChatBotFlagService()
        self._ai_client: Optional[NvidiaAIClient] = None

    async def _get_ai_client(self) -> NvidiaAIClient:
        """Get or create AI client."""
        if self._ai_client is None:
            self._ai_client = NvidiaAIClient()
        return self._ai_client

    async def can_use_ai(self, telegram_id: int) -> bool:
        """Check if user can use AI chat bot."""
        # Check if AI mode is enabled globally
        if not await self.flag_service.is_enabled():
            logger.debug("AI chat bot mode is disabled globally")
            return False

        # Check if user is admin
        if not await UserService.is_user_admin(telegram_id):
            logger.debug("User %s is not admin, cannot use AI", telegram_id)
            return False

        logger.debug("User %s can use AI chat bot", telegram_id)
        return True

    async def prompt_ai(self, telegram_id: int, prompt: str) -> Optional[str]:
        """Send prompt to AI if user has permission."""
        if not await self.can_use_ai(telegram_id):
            logger.info("User %s attempted to use AI but lacks permission", telegram_id)
            return None

        try:
            ai_client = await self._get_ai_client()
            response = await ai_client.simple_prompt(prompt)
            logger.info("AI response generated for user %s", telegram_id)
            return response
        except Exception as e:
            logger.error("Error generating AI response for user %s: %s", telegram_id, e)
            return None

    async def enable_ai_mode(self) -> bool:
        """Enable AI chat bot mode globally."""
        return await self.flag_service.enable()

    async def disable_ai_mode(self) -> bool:
        """Disable AI chat bot mode globally."""
        return await self.flag_service.disable()

    async def is_ai_mode_enabled(self) -> bool:
        """Check if AI chat bot mode is enabled globally."""
        return await self.flag_service.is_enabled()

    async def close(self):
        """Close connections."""
        if self._ai_client:
            await self._ai_client.close()
        await self.flag_service.close()