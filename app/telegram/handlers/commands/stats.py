from telegram import Update, ForceReply
from telegram.ext import ContextTypes

from config.log_setup import get_logger

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

    await update.message.reply_html(
        rf"Hi {mention}! Here are the cache stats: {stats}",
        reply_markup=ForceReply(selective=True)
    )
