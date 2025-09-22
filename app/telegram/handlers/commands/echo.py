"""Echo handler for non-command messages."""
from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from app.telegram.utils import is_valid_station_id

logger = get_logger(__name__)

async def echo_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command text messages with simple echo."""
    if not update.message or not update.message.text:
        return

    message_text = update.message.text.strip()
    
    # If the message is a valid station id, prompt to use the commands
    if is_valid_station_id(message_text):
        await update.message.reply_text(
            f"I see you sent a station ID: {message_text}\n\n"
            "To get information, please use one of these commands:\n"
            f"• /schedule {message_text} - Get station schedule\n"
            f"• /search {message_text} <to_station> - Search routes"
        )
    else:
        # Simple echo for other messages
        await update.message.reply_text(f"Echo: {message_text}")