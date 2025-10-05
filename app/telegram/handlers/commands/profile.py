"""Profile command: shows user info from DB."""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from services.database.user_service import UserService
from app.telegram.messages import get_message
from app.telegram.utils import escape_markdown_v2


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

    # Escape user data for MarkdownV2
    username = escape_markdown_v2(db_user.username) if db_user.username else not_set
    first_name = escape_markdown_v2(db_user.first_name) if db_user.first_name else not_set
    last_name = escape_markdown_v2(db_user.last_name) if db_user.last_name else not_set
    base_title = escape_markdown_v2(db_user.base_station_title) if db_user.base_station_title else not_set
    base_code = escape_markdown_v2(db_user.base_station_code) if db_user.base_station_code else not_set
    dest_title = escape_markdown_v2(db_user.destination_title) if db_user.destination_title else not_set
    dest_code = escape_markdown_v2(db_user.destination_code) if db_user.destination_code else not_set

    msg = (
        f"{header}\n"
        f"{separator}\n\n"
        f"🏷️ {username_label} {username}\n"
        f"📛 {first_name_label} {first_name}\n"
        f"📛 {last_name_label} {last_name}\n\n"
        f"🏠 {base_station_label} {base_title}\n"
        f"     🔗 {code_label} {base_code}\n\n"
        f"🎯 {destination_label} {dest_title}\n"
        f"     🔗 {code_label} {dest_code}"
    )
    await update.message.reply_text(msg)


# For registry
slug = "profile"
function = profile_command
