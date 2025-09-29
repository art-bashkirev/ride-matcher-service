"""AI mode toggle command for admin users."""

from telegram import Update
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from config.settings import get_config
from services.database.user_service import UserService
from services.ai.flag_service import AIFlagService

logger = get_logger(__name__)

slug = "ai_mode"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ai_mode command (admin only)."""
    if update.message is None or update.effective_user is None:
        logger.debug("Ignoring ai_mode command without message or user")
        return
    
    user = update.effective_user
    user_info = user.username if user else "unknown"
    
    config = get_config()
    if config.is_development:
        logger.info("AI mode command invoked by user %s", user_info)
    
    logger.info("User %s requested ai_mode command", user_info)

    # Check if user exists and is admin
    try:
        db_user = await UserService.get_user(user.id)
        if not db_user:
            logger.warning("User %s attempted to use ai_mode without starting bot first", user_info)
            await update.message.reply_text("You need to start the bot first with /start")
            return
        
        if not db_user.is_admin:
            logger.warning("Non-admin user %s attempted to use ai_mode command", user_info)
            await update.message.reply_text("This command is only available to administrators.")
            return
    except Exception as e:
        logger.error("Database error while checking user %s for ai_mode command: %s", user_info, e)
        await update.message.reply_text("❌ Unable to verify user permissions. Please try again later.")
        return

    # Parse command arguments
    args = context.args if context.args else []
    
    if not args:
        # Show current status
        try:
            async with AIFlagService() as flag_service:
                current_status = await flag_service.is_ai_mode_enabled()
            
            status_text = "enabled" if current_status else "disabled"
            await update.message.reply_text(
                f"AI mode is currently *{status_text}*\n\n"
                f"Use `/ai_mode on` to enable or `/ai_mode off` to disable AI mode.",
                parse_mode="Markdown"
            )
            logger.debug("AI mode status shown to admin user %s: %s", user_info, status_text)
        except Exception as e:
            logger.error("Failed to check AI mode status for user %s: %s", user_info, e)
            await update.message.reply_text("❌ Unable to check AI mode status. Please try again later.")
        return
    
    command = args[0].lower()
    
    if command not in ["on", "off", "enable", "disable", "true", "false"]:
        logger.warning("Invalid ai_mode command from user %s: %s", user_info, command)
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
    try:
        async with AIFlagService() as flag_service:
            success = await flag_service.set_ai_mode(enable_ai)
        
        if success:
            status_text = "enabled" if enable_ai else "disabled"
            await update.message.reply_text(
                f"✅ AI mode has been *{status_text}*",
                parse_mode="Markdown"
            )
            logger.info("Admin user %s successfully changed AI mode to: %s", user_info, enable_ai)
        else:
            await update.message.reply_text("❌ Failed to update AI mode. Please try again later.")
            logger.error("Failed to update AI mode for admin user %s (operation returned false)", user_info)
    except Exception as e:
        logger.error("Exception while updating AI mode for admin user %s: %s", user_info, e)
        await update.message.reply_text("❌ An error occurred while updating AI mode. Please try again later.")