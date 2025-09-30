"""AI mode toggle command for admin users."""

from telegram import Update
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from config.settings import get_config
from services.database.user_service import UserService
from services.ai.flag_service import AIFlagService
from app.telegram.messages import get_message

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
            await update.message.reply_text(get_message("ai_mode_start_required"))
            return
        
        if not db_user.is_admin:
            logger.warning("Non-admin user %s attempted to use ai_mode command", user_info)
            await update.message.reply_text(get_message("ai_mode_admin_only"))
            return
    except Exception as e:
        logger.error("Database error while checking user %s for ai_mode command: %s", user_info, e)
        await update.message.reply_text(get_message("ai_mode_permission_error"))
        return

    # Parse command arguments
    args = context.args if context.args else []
    
    if not args:
        # Show current status
        try:
            async with AIFlagService() as flag_service:
                current_status = await flag_service.is_ai_mode_enabled()
            
            status_word = get_message("ai_mode_status_enabled" if current_status else "ai_mode_status_disabled")
            status_text = get_message("ai_mode_status", status=status_word)
            usage_hint = get_message("ai_mode_usage_hint")
            await update.message.reply_text(
                f"{status_text}\n\n{usage_hint}",
                parse_mode="Markdown"
            )
            logger.debug("AI mode status shown to admin user %s: %s", user_info, status_text)
        except Exception as e:
            logger.error("Failed to check AI mode status for user %s: %s", user_info, e)
            await update.message.reply_text(get_message("ai_mode_error_checking"))
        return
    
    command = args[0].lower()
    
    if command not in ["on", "off", "enable", "disable", "true", "false"]:
        logger.warning("Invalid ai_mode command from user %s: %s", user_info, command)
        await update.message.reply_text(
            get_message("ai_mode_invalid_command"),
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
            status_word = get_message("ai_mode_status_enabled" if enable_ai else "ai_mode_status_disabled")
            await update.message.reply_text(
                get_message("ai_mode_updated", status=status_word),
                parse_mode="Markdown"
            )
            logger.info("Admin user %s successfully changed AI mode to: %s", user_info, enable_ai)
        else:
            await update.message.reply_text(get_message("ai_mode_update_failed"))
            logger.error("Failed to update AI mode for admin user %s (operation returned false)", user_info)
    except Exception as e:
        logger.error("Exception while updating AI mode for admin user %s: %s", user_info, e)
        await update.message.reply_text(get_message("ai_mode_error_updating"))