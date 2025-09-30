from telegram import Update, ForceReply
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from app.telegram.messages import get_message

from services.yandex_schedules.cached_client import CachedYandexSchedules

logger = get_logger(__name__)

slug = "stats"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command."""
    if update.message is None:
        return
    user = update.effective_user
    mention = user.mention_html() if user else "there"
    logger.info("User %s requested stats", user.username if user else "unknown")

    async with CachedYandexSchedules() as client:
        stats = await client.get_cache_stats()

    title = get_message("stats_title")
    separator = get_message("separator")
    intro = get_message("stats_intro", mention=mention)
    stats_body = get_message("stats_message", stats=stats)
    tip = get_message("stats_tip")

    message_text = (
        f"{title}\n"
        f"{separator}\n\n"
        f"{intro}\n\n"
        f"{stats_body}\n\n"
        f"{tip}"
    )

    await update.message.reply_html(
        message_text,
        reply_markup=ForceReply(selective=True)
    )
