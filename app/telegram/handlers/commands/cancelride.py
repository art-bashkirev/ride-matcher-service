"""Cancel Ride command: Cancel active ride matching search."""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config.log_setup import get_logger
from services.mongodb.thread_matching_service import get_thread_matching_service
from app.telegram.messages import get_message

logger = get_logger(__name__)


async def cancelride_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel user's active ride matching search."""
    user = update.effective_user
    telegram_id = getattr(user, "id", None)

    if telegram_id is None or update.message is None:
        logger.warning("cancelride_command called with no user or message")
        return

    # Log command invocation
    logger.info(
        "User %s (username: %s) invoked /cancelride command",
        telegram_id,
        getattr(user, "username", "unknown"),
    )

    try:
        # Clear search results from MongoDB
        thread_service = get_thread_matching_service()
        success = await thread_service.clear_search_results(telegram_id)

        if success:
            logger.info("User %s successfully cancelled ride search", telegram_id)
            await update.message.reply_text(get_message("ride_cancel_success"))
        else:
            logger.debug("User %s had no active ride search to cancel", telegram_id)
            await update.message.reply_text(get_message("ride_cancel_nothing"))

    except Exception as e:
        logger.error(
            "Error in cancelride_command for user %s: %s", telegram_id, e, exc_info=True
        )
        await update.message.reply_text(get_message("ride_search_error"))


# For registry
slug = "cancelride"
function = cancelride_command
