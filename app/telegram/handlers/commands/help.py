from telegram import Update
from telegram.ext import ContextTypes

from app.telegram.i18n import get_i18n_manager
from config.log_setup import get_logger

logger = get_logger(__name__)

slug = "help"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    if not update.message:
        return
    
    user = update.effective_user
    telegram_id = getattr(user, "id", None) if user else None
    
    i18n = get_i18n_manager()
    
    # Get user language from DB, cache, or Telegram locale
    user_language = None
    if telegram_id:
        telegram_locale = user.language_code if user and hasattr(user, 'language_code') else None
        user_language = await i18n.get_user_language_preference(telegram_id, telegram_locale)
    
    logger.info("User %s requested help", user.username if user else "unknown")
    
    # Build help message using i18n
    title = i18n.get_message("help_title", telegram_id, user_language)
    separator = "═══════════════════════"
    commands = i18n.get_message("help_commands", telegram_id, user_language)
    need_help = i18n.get_message("help_need_help", telegram_id, user_language)
    
    await update.message.reply_text(
        f"{title}\n"
        f"{separator}\n"
        f"{commands}\n\n"
        f"{need_help}"
    )
