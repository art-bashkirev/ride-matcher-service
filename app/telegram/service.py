from __future__ import annotations
import asyncio
from contextlib import suppress
from typing import Optional

from telegram.ext import Application

from .config import TelegramSettings
from .handlers.registry import HandlerRegistry
from config.log_setup import get_logger

logger = get_logger(__name__)

class TelegramBotService:
    """Service class wrapping python-telegram-bot with explicit async lifecycle."""

    def __init__(self, settings: Optional[TelegramSettings] = None):
        self.settings = settings or TelegramSettings.load()
        self._application: Optional[Application] = None

    def build(self):
        if not self.settings.token:
            return None
        app = Application.builder().token(self.settings.token).build()
        
        # Register all handlers through the registry
        registry = HandlerRegistry()
        registry.register_all(app)
        
        return app

    @property
    def application(self) -> Optional[Application]:
        return self._application

    async def start(self):
        if not self.settings.enabled or not self.settings.token:
            logger.info("Telegram bot disabled (no token)")
            return
        if self._application:
            logger.debug("Telegram bot already running")
            return
        self._application = self.build()
        if not self._application:
            return
        app = self._application
        await app.initialize()
        await app.start()
        updater = getattr(app, "updater", None)
        if updater:
            await updater.start_polling()
        logger.info("Telegram bot started (polling)")

    async def stop(self):
        if not self._application:
            return
        logger.info("Stopping Telegram bot")
        app = self._application
        with suppress(Exception):
            updater = getattr(app, "updater", None)
            if updater:
                await updater.stop()
            await app.stop()
            await app.shutdown()
        logger.info("Telegram bot stopped")
