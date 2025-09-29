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
        f"👤 **Profile Information**\n"
        f"═══════════════════════\n\n"
        f"🏷️ **Username:** {db_user.username or 'Not set'}\n"
        f"👨‍💼 **First Name:** {db_user.first_name or 'Not set'}\n"
        f"👨‍💼 **Last Name:** {db_user.last_name or 'Not set'}\n\n"
        f"📍 **Base Station:** {db_user.base_station_title or 'Not set'}\n"
        f"     🔗 Code: {db_user.base_station_code or 'Not set'}\n\n"
        f"🎯 **Destination:** {db_user.destination_title or 'Not set'}\n"
        f"     🔗 Code: {db_user.destination_code or 'Not set'}"
    )
    await update.message.reply_text(msg)

# For registry
slug = "profile"
function = profile_command
