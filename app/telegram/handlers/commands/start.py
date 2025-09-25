from telegram import Update, ForceReply
from telegram.ext import ContextTypes

from config.log_setup import get_logger

logger = get_logger(__name__)

slug = "start"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
