"""Handler registry for automatic registration of Telegram bot handlers."""
from __future__ import annotations
from typing import List, Dict, Any
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from .commands import cmd_start, cmd_help, cmd_schedule, echo_text


class HandlerRegistry:
    """Registry for organizing and registering Telegram bot handlers."""
    
    def __init__(self):
        self._command_handlers: Dict[str, Any] = {
            "start": cmd_start,
            "help": cmd_help, 
            "schedule": cmd_schedule,
        }
        
        self._message_handlers: List[tuple] = [
            # (filter, handler_function)
            (filters.TEXT & ~filters.COMMAND, echo_text),
        ]
    
    def register_all(self, app: Application) -> None:
        """Register all handlers with the application."""
        self._register_command_handlers(app)
        self._register_message_handlers(app)
    
    def _register_command_handlers(self, app: Application) -> None:
        """Register all command handlers."""
        for command, handler in self._command_handlers.items():
            app.add_handler(CommandHandler(command, handler))
    
    def _register_message_handlers(self, app: Application) -> None:
        """Register all message handlers."""
        for filter_obj, handler in self._message_handlers:
            app.add_handler(MessageHandler(filter_obj, handler))
    
    def add_command(self, command: str, handler: Any) -> None:
        """Add a new command handler to the registry."""
        self._command_handlers[command] = handler
    
    def add_message_handler(self, filter_obj: Any, handler: Any) -> None:
        """Add a new message handler to the registry."""
        self._message_handlers.append((filter_obj, handler))