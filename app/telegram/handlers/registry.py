"""Handler registry for automatic registration of Telegram bot handlers."""
from __future__ import annotations

import importlib
import pkgutil
from typing import List

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters

from app.telegram.handlers.callbacks import handle_schedule_pagination, handle_noop_callback, handle_schedule_from_search
from app.telegram.handlers.commands.echo_text import function as echo_text


class HandlerRegistry:
    """Registry for organizing and registering Telegram bot handlers."""

    def __init__(self):
        # Only message handlers need to be listed explicitly
        self._message_handlers: List[tuple] = [
            (filters.TEXT & ~filters.COMMAND, echo_text),
        ]

        # Callback query handlers for inline keyboards  
        self._callback_handlers: List[tuple] = [
            ("schedule_page:", handle_schedule_pagination),
            ("schedule_s", handle_schedule_from_search),  # Matches "schedule_s1234567"
            ("noop", handle_noop_callback),
        ]

        # Conversation handlers
        self._conversation_handlers: List[ConversationHandler] = []

    def register_all(self, app: Application) -> None:
        """Register all handlers with the application."""
        self._register_command_handlers(app)
        self._register_conversation_handlers(app)
        self._register_callback_handlers(app)
        self._register_message_handlers(app)

    def _register_command_handlers(self, app: Application) -> None:
        """Auto-discover and register all command handlers from commands/*.py."""
        from . import commands
        package = commands
        for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
            if is_pkg:
                continue
            mod = importlib.import_module(f"{package.__name__}.{module_name}")
            slug = getattr(mod, "slug", None)
            func = getattr(mod, "function", None)
            if slug and func:
                # Check if it's a ConversationHandler
                if isinstance(func, ConversationHandler):
                    self._conversation_handlers.append(func)
                else:
                    app.add_handler(CommandHandler(slug, func))

    def _register_conversation_handlers(self, app: Application) -> None:
        """Register conversation handlers."""
        for handler in self._conversation_handlers:
            app.add_handler(handler)

    def _register_message_handlers(self, app: Application) -> None:
        for filter_obj, handler in self._message_handlers:
            app.add_handler(MessageHandler(filter_obj, handler))

    def _register_callback_handlers(self, app: Application) -> None:
        """Register callback query handlers for inline keyboards."""
        for pattern, handler in self._callback_handlers:
            app.add_handler(CallbackQueryHandler(handler, pattern=f"^{pattern}"))
