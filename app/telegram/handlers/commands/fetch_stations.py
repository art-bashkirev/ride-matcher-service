"""Fetch and store all stations from Yandex API."""

from telegram import Update
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from services.yandex_schedules.cached_client import CachedYandexSchedules
from services.yandex_schedules.models.stations_list import StationsListRequest
from services.database.stations_service import get_stations_service

logger = get_logger(__name__)

slug = "fetch_stations"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fetch_stations command - manual refresh operation."""
    if not update.message:
        return

    username = update.effective_user.username if update.effective_user else "unknown"
    
    # Show loading message
    loading_message = await update.message.reply_text(
        "⏳ Manually refreshing stations data from Yandex API...\n"
        "This will update the stations database with the latest data."
    )

    logger.info("User %s requested manual stations refresh", username)

    try:
        stations_service = get_stations_service()
        current_count = await stations_service.get_stations_count()
        
        # Fetch stations from Yandex API
        async with CachedYandexSchedules() as client:
            stations_response = await client.get_stations_list(StationsListRequest())

        # Store in MongoDB
        stored_count = await stations_service.flatten_and_store_stations(stations_response)

        success_message = (
            f"✅ Successfully refreshed stations data!\n\n"
            f"📊 **Statistics:**\n"
            f"• Previous stations: {current_count:,}\n"
            f"• New stations stored: {stored_count:,}\n"
            f"• Countries: {len(stations_response.countries)}\n"
            f"• Total regions: {sum(len(country.regions) for country in stations_response.countries)}\n"
            f"• Total settlements: {sum(len(region.settlements) for country in stations_response.countries for region in country.regions)}\n\n"
            f"🔍 Station search is ready to use with updated data!"
        )

        await loading_message.edit_text(success_message)
        
        logger.info("Successfully refreshed and stored %d stations for user %s", stored_count, username)

    except Exception as e:
        logger.error("Error refreshing stations: %s", str(e))

        error_message = (
            f"❌ Error refreshing stations from Yandex API\n"
            f"Please try again later or contact support.\n\n"
            f"Error details: {str(e)}"
        )

        try:
            await loading_message.edit_text(error_message)
        except Exception:
            await update.message.reply_text(error_message)