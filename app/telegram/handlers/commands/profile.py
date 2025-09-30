"""Profile command: shows user info from DB."""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from services.database.user_service import UserService
from app.telegram.i18n import get_i18n_manager, Language

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = getattr(user, "id", None)
    if telegram_id is None or update.message is None:
        return
    
    i18n = get_i18n_manager()
    
    # Get user language from DB, cache, or Telegram locale
    telegram_locale = user.language_code if user and hasattr(user, 'language_code') else None
    user_language = await i18n.get_user_language_preference(telegram_id, telegram_locale)
    
    db_user = await UserService.get_user(telegram_id)
    if not db_user:
        not_found_msg = i18n.get_message("profile_not_found", telegram_id, user_language)
        await update.message.reply_text(not_found_msg)
        return
    
    # Build profile message using i18n
    header = i18n.get_message("profile_title", telegram_id, user_language)
    separator = "═══════════════════════"
    
    username_label = i18n.get_message("profile_username", telegram_id, user_language)
    first_name_label = i18n.get_message("profile_first_name", telegram_id, user_language)
    last_name_label = i18n.get_message("profile_last_name", telegram_id, user_language)
    base_station_label = i18n.get_message("profile_base_station", telegram_id, user_language)
    destination_label = i18n.get_message("profile_destination", telegram_id, user_language)
    code_label = i18n.get_message("profile_code", telegram_id, user_language)
    not_set = i18n.get_message("profile_not_set", telegram_id, user_language)
    
    msg = (
        f"{header}\n"
        f"{separator}\n\n"
        f"🏷️ {username_label} {db_user.username or not_set}\n"
        f"📛 {first_name_label} {db_user.first_name or not_set}\n"
        f"📛 {last_name_label} {db_user.last_name or not_set}\n\n"
        f"🏠 {base_station_label} {db_user.base_station_title or not_set}\n"
        f"     🔗 {code_label} {db_user.base_station_code or not_set}\n\n"
        f"🎯 {destination_label} {db_user.destination_title or not_set}\n"
        f"     🔗 {code_label} {db_user.destination_code or not_set}"
    )
    await update.message.reply_text(msg)

# For registry
slug = "profile"
function = profile_command
