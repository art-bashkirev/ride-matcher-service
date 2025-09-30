from telegram import Update
from telegram.ext import ContextTypes

from app.telegram.messages import get_message
from config.log_setup import get_logger

logger = get_logger(__name__)

slug = "help"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    if not update.message:
        return
    
    user = update.effective_user
    logger.info("User %s requested help", user.username if user else "unknown")
    
    # Build help message
    title = get_message("help_title")
    separator = "═══════════════════════"
    commands = get_message("help_commands")
    need_help = get_message("help_need_help")
    
    await update.message.reply_text(
        f"{title}\n"
        f"{separator}\n"
        f"{commands}\n\n"
        f"{need_help}"
    )
