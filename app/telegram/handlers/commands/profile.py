"""Profile command: shows user info from DB."""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from services.database.user_service import UserService
from app.telegram.messages import get_message


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = getattr(user, "id", None)
    if telegram_id is None or update.message is None:
        return

    db_user = await UserService.get_user(telegram_id)
    if not db_user:
        not_found_msg = get_message("profile_not_found")
        await update.message.reply_text(not_found_msg)
        return

    # Build profile message
    header = get_message("profile_title")
    separator = get_message("separator")

    username_label = get_message("profile_username")
    first_name_label = get_message("profile_first_name")
    last_name_label = get_message("profile_last_name")
    base_station_label = get_message("profile_base_station")
    destination_label = get_message("profile_destination")
    code_label = get_message("profile_code")
    not_set = get_message("profile_not_set")

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
