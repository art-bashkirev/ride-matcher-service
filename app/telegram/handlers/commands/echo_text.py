from telegram import Update
from telegram.ext import ContextTypes
from app.telegram.utils import is_valid_station_id

async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command text messages."""
    if not update.message or not update.message.text:
        return
    message_text = update.message.text.strip()
    if is_valid_station_id(message_text):
        await update.message.reply_text(f"Use /schedule {message_text} for schedule info.")
    else:
        await update.message.reply_text(f"Echo: {message_text}")
