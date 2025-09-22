"""Command handlers for Telegram bot."""
from __future__ import annotations
from telegram import Update, ForceReply
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from app.telegram.utils import is_valid_station_id

logger = get_logger(__name__)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    if update.message is None:
        return
    
    user = update.effective_user
    mention = user.mention_html() if user else "there"
    logger.info("User %s started the bot", user.username if user else "unknown")
    
    await update.message.reply_html(
        rf"Hi {mention}! This is a placeholder bot.",
        reply_markup=ForceReply(selective=True)
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    if not update.message:
        return
    
    logger.info("User %s requested help", update.effective_user.username if update.effective_user else "unknown")
    await update.message.reply_text("Available commands: /start, /help, /schedule")

async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /schedule command - placeholder."""
    if not update.message:
        return
    
    logger.info("User %s requested schedule", update.effective_user.username if update.effective_user else "unknown")
    
    if not context.args:
        await update.message.reply_text("Please provide a station id, e.g. /schedule s1234567")
        return
    
    station_id = context.args[0]
    
    if not is_valid_station_id(station_id):
        await update.message.reply_text(f"Invalid station ID format: {station_id}")
        return
    
    await update.message.reply_text(f"Schedule placeholder for station: {station_id}")

async def echo_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command text messages."""
    if not update.message or not update.message.text:
        return

    message_text = update.message.text.strip()
    
    if is_valid_station_id(message_text):
        await update.message.reply_text(f"Use /schedule {message_text} for schedule info.")
    else:
        await update.message.reply_text(f"Echo: {message_text}")
