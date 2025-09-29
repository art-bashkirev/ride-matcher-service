"""Admin user management commands."""

from telegram import Update
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from services.database.user_service import UserService

logger = get_logger(__name__)

slug = "setadmin"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setadmin command for managing admin status (admin only)."""
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
            "❌ You don't have admin privileges to manage user admin status."
        )
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage: `/setadmin <telegram_id> <true|false>`\n\n"
            "Example: `/setadmin 123456789 true`"
        )
        return

    try:
        target_telegram_id = int(context.args[0])
        is_admin_str = context.args[1].lower()
        
        if is_admin_str not in ['true', 'false']:
            await update.message.reply_text(
                "❌ Admin status must be 'true' or 'false'."
            )
            return
        
        is_admin = is_admin_str == 'true'
        
        # Check if target user exists
        target_user = await UserService.get_user(target_telegram_id)
        if not target_user:
            await update.message.reply_text(
                f"❌ User with Telegram ID {target_telegram_id} not found in database."
            )
            return
        
        # Update admin status
        updated_user = await UserService.set_user_admin(target_telegram_id, is_admin)
        if updated_user:
            status_text = "granted" if is_admin else "revoked"
            await update.message.reply_text(
                f"✅ Admin privileges {status_text} for user {target_telegram_id}"
                f"{f' (@{target_user.username})' if target_user.username else ''}."
            )
            logger.info(
                "User %s set admin status for user %s to %s", 
                user.username or telegram_id, 
                target_telegram_id, 
                is_admin
            )
        else:
            await update.message.reply_text("❌ Failed to update admin status.")

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid Telegram ID. Please provide a valid number."
        )
    except Exception as e:
        logger.error("Error in setadmin command for user %s: %s", telegram_id, e)
        await update.message.reply_text(
            "❌ An error occurred while updating admin status."
        )