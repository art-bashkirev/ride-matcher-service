from telegram import Update, ForceReply
from telegram.ext import ContextTypes

from app.telegram.i18n import get_i18n_manager
from config.log_setup import get_logger

logger = get_logger(__name__)

slug = "start"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    if update.message is None:
        return
    
    user = update.effective_user
    telegram_id = getattr(user, "id", None) if user else None
    mention = user.mention_html() if user else "there"
    
    i18n = get_i18n_manager()
    
    # Detect user language
    user_language = None
    if user and hasattr(user, 'language_code') and user.language_code:
        user_language = i18n.detect_language_from_locale(user.language_code)
    
    logger.info("User %s started the bot", user.username if user else "unknown")
    
    # Build welcome message using i18n
    welcome = i18n.get_message("start_welcome", telegram_id, user_language)
    get_started = i18n.get_message("start_get_started", telegram_id, user_language)
    ready = i18n.get_message("start_ready", telegram_id, user_language)
    
    await update.message.reply_html(
        f"{welcome}\n\n"
        f"Hi {mention}! I'm here to help you with train schedules and station information.\n\n"
        f"{get_started}\n"
        f"• Use /help to see all available commands\n"
        f"• Use /setstations to configure your stations\n"
        f"• Use /schedule to check train times\n\n"
        f"{ready}",
        reply_markup=ForceReply(selective=True)
    )
