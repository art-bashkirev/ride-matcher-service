from telegram import Update
from telegram.ext import ContextTypes

from config.log_setup import get_logger

logger = get_logger(__name__)

slug = "help"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    if not update.message:
        return
    logger.info("User %s requested help", update.effective_user.username if update.effective_user else "unknown")
    
    help_text = (
        "Available commands:\n"
        "• /start - Start the bot\n"
        "• /help - Show this help message\n"
        "• /schedule - Get schedule information\n"
        "• /stats - Show bot statistics\n"
        "• /ai <prompt> - Chat with AI (admin only)\n"
        "• /aimode [enable|disable|status] - Manage AI mode (admin only)\n"
        "• /setadmin <telegram_id> <true|false> - Manage admin status (admin only)"
    )
    
    await update.message.reply_text(help_text)
