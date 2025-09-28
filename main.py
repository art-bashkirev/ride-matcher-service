import asyncio

from app.api.service import ApiServerService
from app.telegram.service import TelegramBotService
from config.log_setup import get_logger
from config.settings import get_config
from services.database.user_service import UserService

logger = get_logger(__name__)


async def main():
    cfg = get_config()
    logger.info("Service starting (env=%s)", cfg.environment)

    # Initialize database
    await UserService.init_db()
    logger.info("Database initialized")

    api = ApiServerService()
    bot = TelegramBotService()
    await api.start()
    await bot.start()
    logger.info("Service started. (No graceful shutdown handlers; Ctrl+C to terminate process)")
    # Sleep forever
    await asyncio.Future()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
