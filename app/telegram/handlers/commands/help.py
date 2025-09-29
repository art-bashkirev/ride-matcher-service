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
    await update.message.reply_text(
        "🤖 **Available Commands**\n"
        "═══════════════════════\n\n"
        "🚀 /start - Initialize the bot\n"
        "❓ /help - Show this help message\n"
        "🚂 /schedule - View train schedules\n"
        "📊 /stats - View cache statistics\n"
        "👤 /profile - View your profile\n"
        "⚙️ /setstations - Set your stations\n\n"
        "💡 **Need help?** Just type a command to get started!"
    )
