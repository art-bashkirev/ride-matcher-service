from telegram import Update
from telegram.ext import ContextTypes
from config.log_setup import get_logger
from app.telegram.utils import is_valid_station_id

logger = get_logger(__name__)

slug = "schedule"

async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
