from telegram import Update
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from app.telegram.messages import get_message

logger = get_logger(__name__)

slug = "test"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /test command."""
    if not update.message:
        return
    logger.info(
        "User %s requested test",
        update.effective_user.username if update.effective_user else "unknown",
    )
    title = get_message("test_title")
    separator = get_message("separator")
    quote = get_message("test_quote")
    working = get_message("test_working")

    message_text = f"{title}\n" f"{separator}\n\n" f"{quote}\n\n" f"{working}"

    await update.message.reply_text(message_text)
