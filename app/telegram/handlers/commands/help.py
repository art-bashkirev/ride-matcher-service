"""Help command handler."""
from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes

from config.log_setup import get_logger

logger = get_logger(__name__)

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    if not update.message:
        return
    
    logger.info("User %s requested help", update.effective_user.username if update.effective_user else "unknown")
    
    help_text = """
Available commands (placeholder implementations):
/start - Start the bot
/help - Show this help message
/schedule <station_id> - Get station schedule (placeholder)
/search <from> <to> [date] - Search routes (placeholder)

This is a placeholder bot implementation. Commands will echo back with confirmation.
"""
    
    await update.message.reply_text(help_text.strip())