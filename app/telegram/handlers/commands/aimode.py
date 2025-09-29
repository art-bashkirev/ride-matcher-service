"""Admin commands for AI chat bot management."""

from telegram import Update
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from services.ai.ai_service import AIChatBotService
from services.database.user_service import UserService

logger = get_logger(__name__)

slug = "aimode"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /aimode command for AI mode management (admin only)."""
    if not update.message or not update.effective_user:
        return

    user = update.effective_user
    telegram_id = user.id
    
    # Ensure user exists in database
    await UserService.get_or_create_user(
        telegram_id=telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    # Check if user is admin
    if not await UserService.is_user_admin(telegram_id):
        await update.message.reply_text(
            "❌ You don't have admin privileges to manage AI mode."
        )
        return

    ai_service = AIChatBotService()
    
    try:
        if not context.args:
            # Show current status
            status = await ai_service.is_ai_mode_enabled()
            status_text = "enabled" if status else "disabled"
            await update.message.reply_text(
                f"🤖 AI chat mode is currently **{status_text}**.\n\n"
                f"Usage:\n"
                f"• `/aimode enable` - Enable AI mode\n"
                f"• `/aimode disable` - Disable AI mode\n"
                f"• `/aimode status` - Show current status"
            )
            return

        command = context.args[0].lower()
        
        if command == "enable":
            success = await ai_service.enable_ai_mode()
            if success:
                await update.message.reply_text("✅ AI chat mode has been enabled.")
                logger.info("User %s enabled AI mode", user.username or telegram_id)
            else:
                await update.message.reply_text("❌ Failed to enable AI mode.")
        
        elif command == "disable":
            success = await ai_service.disable_ai_mode()
            if success:
                await update.message.reply_text("✅ AI chat mode has been disabled.")
                logger.info("User %s disabled AI mode", user.username or telegram_id)
            else:
                await update.message.reply_text("❌ Failed to disable AI mode.")
        
        elif command == "status":
            status = await ai_service.is_ai_mode_enabled()
            status_text = "enabled" if status else "disabled"
            await update.message.reply_text(f"🤖 AI chat mode is currently **{status_text}**.")
        
        else:
            await update.message.reply_text(
                "❌ Invalid command. Use `enable`, `disable`, or `status`."
            )

    except Exception as e:
        logger.error("Error in aimode command for user %s: %s", telegram_id, e)
        await update.message.reply_text(
            "❌ An error occurred while managing AI mode."
        )
    
    finally:
        await ai_service.close()