"""Schedule command handler - placeholder implementation."""
from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from app.telegram.utils import is_valid_station_id

logger = get_logger(__name__)

async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /schedule command - placeholder implementation."""
    if not update.message:
        return
    
    logger.info("User %s requested schedule", update.effective_user.username if update.effective_user else "unknown")
    
    if not context.args:
        await update.message.reply_text(
            "Please provide a station id after the command, e.g. /schedule s1234567"
        )
        return
    
    station_id = context.args[0]
    
    if not is_valid_station_id(station_id):
        await update.message.reply_text(
            f"Invalid station ID format: {station_id}. "
            "Station ID should be in format 's' followed by 7 digits (e.g., s1234567)"
        )
        return
    
    # Placeholder implementation - just echo back with confirmation
    await update.message.reply_text(
        f"📅 Schedule Request (Placeholder)\n\n"
        f"Station ID: {station_id}\n"
        f"Command: /schedule\n\n"
        f"This is a placeholder implementation. In the future, this will show "
        f"real schedule data from Yandex Schedules API."
    )