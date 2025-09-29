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
        f"🎉 **Welcome to Ride Matcher!** 🎉\n\n"
        f"Hi {mention}! I'm here to help you with train schedules and station information.\n\n"
        f"🚀 **Get Started:**\n"
        f"• Use /help to see all available commands\n"
        f"• Use /setstations to configure your stations\n"
        f"• Use /schedule to check train times\n\n"
        f"📱 Ready to explore? Type /help to begin!",
        reply_markup=ForceReply(selective=True)
    )
