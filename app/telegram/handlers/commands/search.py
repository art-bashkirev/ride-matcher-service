"""Search command handler - placeholder implementation."""
from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from app.telegram.utils import is_valid_station_id

logger = get_logger(__name__)

async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command - placeholder implementation."""
    if not update.message:
        return
    
    logger.info("User %s requested search", update.effective_user.username if update.effective_user else "unknown")
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "Please provide from and to station IDs, e.g. /search s1234567 s7654321 [date]"
        )
        return
    
    from_station = context.args[0]
    to_station = context.args[1]
    date_param = context.args[2] if len(context.args) > 2 else "today"
    
    # Validate station IDs
    if not is_valid_station_id(from_station):
        await update.message.reply_text(
            f"Invalid from station ID format: {from_station}. "
            "Station ID should be in format 's' followed by 7 digits (e.g., s1234567)"
        )
        return
    
    if not is_valid_station_id(to_station):
        await update.message.reply_text(
            f"Invalid to station ID format: {to_station}. "
            "Station ID should be in format 's' followed by 7 digits (e.g., s1234567)"
        )
        return
    
    # Placeholder implementation - just echo back with confirmation
    await update.message.reply_text(
        f"🔍 Search Request (Placeholder)\n\n"
        f"From: {from_station}\n"
        f"To: {to_station}\n"
        f"Date: {date_param}\n"
        f"Command: /search\n\n"
        f"This is a placeholder implementation. In the future, this will show "
        f"real search results from Yandex Schedules API."
    )