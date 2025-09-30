from telegram import Update, ForceReply, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from app.telegram.i18n import get_i18n_manager
from config.log_setup import get_logger
from services.database.user_service import UserService

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
    
    # Get user language from DB, cache, or Telegram locale
    user_language = None
    if telegram_id:
        telegram_locale = user.language_code if user and hasattr(user, 'language_code') else None
        user_language = await i18n.get_user_language_preference(telegram_id, telegram_locale)
        
        # Save language to database if we got it from locale
        if telegram_locale and user_language:
            try:
                await UserService.get_or_create_user(telegram_id, user.username, user.first_name, user.last_name)
                await UserService.update_user_language(telegram_id, user_language.value)
            except Exception as e:
                logger.warning(f"Could not save user language: {e}")
    
    logger.info("User %s started the bot", user.username if user else "unknown")
    
    # Check if user has stations configured
    db_user = await UserService.get_user(telegram_id) if telegram_id else None
    has_stations = db_user and db_user.base_station_code and db_user.destination_code
    
    # Build welcome message using i18n
    welcome = i18n.get_message("start_welcome", telegram_id, user_language)
    get_started = i18n.get_message("start_get_started", telegram_id, user_language)
    ready = i18n.get_message("start_ready", telegram_id, user_language)
    
    if has_stations:
        # User has stations - show menu keyboard
        keyboard_base = i18n.get_message("keyboard_schedule_base", telegram_id, user_language)
        keyboard_dest = i18n.get_message("keyboard_schedule_dest", telegram_id, user_language)
        keyboard_help = i18n.get_message("keyboard_help", telegram_id, user_language)
        keyboard_profile = i18n.get_message("keyboard_profile", telegram_id, user_language)
        
        keyboard = [
            [KeyboardButton(f"/schedule {db_user.base_station_code}"), KeyboardButton(f"/schedule {db_user.destination_code}")],
            [KeyboardButton("/help"), KeyboardButton("/profile")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_html(
            f"{welcome}\n\n"
            f"Hi {mention}! I'm here to help you with train schedules.\n\n"
            f"🏠 **Your Base Station:** {db_user.base_station_title}\n"
            f"🎯 **Your Destination:** {db_user.destination_title}\n\n"
            f"Use the menu below to check schedules!",
            reply_markup=reply_markup
        )
    else:
        # User doesn't have stations - prompt to set them
        await update.message.reply_html(
            f"{welcome}\n\n"
            f"Hi {mention}! I'm here to help you with train schedules and station information.\n\n"
            f"{get_started}\n"
            f"• Use /setstations to configure your stations (required)\n"
            f"• Use /help to see all available commands\n\n"
            f"⚠️ Please set your stations first with /setstations to get started!",
            reply_markup=ForceReply(selective=True)
        )
