"""AI mode toggle command for admin users."""

from telegram import Update
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from services.database.user_service import UserService
from services.ai.flag_service import AIFlagService

logger = get_logger(__name__)

slug = "ai_mode"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ai_mode command (admin only)."""
    if update.message is None or update.effective_user is None:
        return
    
    user = update.effective_user
    logger.info("User %s requested ai_mode command", user.username if user else "unknown")

    # Check if user exists and is admin
    db_user = await UserService.get_user(user.id)
    if not db_user:
        await update.message.reply_text("You need to start the bot first with /start")
        return
    
    if not db_user.is_admin:
        await update.message.reply_text("This command is only available to administrators.")
        return

    # Parse command arguments
    args = context.args if context.args else []
    
    if not args:
        # Show current status
        async with AIFlagService() as flag_service:
            current_status = await flag_service.is_ai_mode_enabled()
        
        status_text = "enabled" if current_status else "disabled"
        await update.message.reply_text(
            f"AI mode is currently *{status_text}*\n\n"
            f"Use `/ai_mode on` to enable or `/ai_mode off` to disable AI mode.",
            parse_mode="Markdown"
        )
        return
    
    command = args[0].lower()
    
    if command not in ["on", "off", "enable", "disable", "true", "false"]:
        await update.message.reply_text(
            "Invalid command. Use:\n"
            "• `/ai_mode on` to enable AI mode\n"
            "• `/ai_mode off` to disable AI mode\n"
            "• `/ai_mode` to check current status",
            parse_mode="Markdown"
        )
        return
    
    # Determine the new state
    enable_ai = command in ["on", "enable", "true"]
    
    # Update the flag
    async with AIFlagService() as flag_service:
        success = await flag_service.set_ai_mode(enable_ai)
    
    if success:
        status_text = "enabled" if enable_ai else "disabled"
        await update.message.reply_text(
            f"✅ AI mode has been *{status_text}*",
            parse_mode="Markdown"
        )
        logger.info("Admin user %s changed AI mode to: %s", user.username, enable_ai)
    else:
        await update.message.reply_text("❌ Failed to update AI mode. Please try again later.")
        logger.error("Failed to update AI mode for admin user %s", user.username)