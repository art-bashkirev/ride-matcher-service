from telegram import Update
from telegram.ext import ContextTypes
from config.log_setup import get_logger

logger = get_logger(__name__)

slug = "test"

async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /test command."""
    if not update.message:
        return
    logger.info("User %s requested test", update.effective_user.username if update.effective_user else "unknown")
    await update.message.reply_text("They need us for who we are. So be yourself. Only better.")
