"""Profile command: shows user info from DB."""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from services.database.user_service import UserService

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = getattr(user, "id", None)
    if telegram_id is None or update.message is None:
        return
    db_user = await UserService.get_user(telegram_id)
    if not db_user:
        await update.message.reply_text("No profile found. Please set your stations first with /setstations.")
        return
    msg = (
        f"👤 Profile info:\n"
        f"Username: {db_user.username or '-'}\n"
        f"First name: {db_user.first_name or '-'}\n"
        f"Last name: {db_user.last_name or '-'}\n"
        f"Base station: {db_user.base_station_title or '-'} ({db_user.base_station_code or '-'})\n"
        f"Destination: {db_user.destination_title or '-'} ({db_user.destination_code or '-'})"
    )
    await update.message.reply_text(msg)

# For registry
slug = "profile"
function = CommandHandler("profile", profile_command)
