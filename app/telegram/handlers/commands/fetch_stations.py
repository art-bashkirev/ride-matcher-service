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
    """Handle /fetch_stations command - admin only operation."""
    if not update.message:
        return

    username = update.effective_user.username if update.effective_user else "unknown"
    
    # Show loading message
    loading_message = await update.message.reply_text(
        "⏳ Fetching and storing all stations from Yandex API...\n"
        "This may take a while (large dataset)."
    )

    logger.info("User %s requested stations fetch", username)

    try:
        # Fetch stations from Yandex API
        async with CachedYandexSchedules() as client:
            stations_response = await client.get_stations_list(StationsListRequest())

        # Store in MongoDB
        stations_service = get_stations_service()
        stored_count = await stations_service.flatten_and_store_stations(stations_response)

        success_message = (
            f"✅ Successfully fetched and stored stations!\n\n"
            f"📊 **Statistics:**\n"
            f"• Stations stored: {stored_count:,}\n"
            f"• Countries: {len(stations_response.countries)}\n"
            f"• Total regions: {sum(len(country.regions) for country in stations_response.countries)}\n"
            f"• Total settlements: {sum(len(region.settlements) for country in stations_response.countries for region in country.regions)}\n\n"
            f"You can now use /search_station to find stations!"
        )

        await loading_message.edit_text(success_message)
        
        logger.info("Successfully fetched and stored %d stations for user %s", stored_count, username)

    except Exception as e:
        logger.error("Error fetching stations: %s", str(e))

        error_message = (
            f"❌ Error fetching stations from Yandex API\n"
            f"Please try again later or contact support.\n\n"
            f"Error details: {str(e)}"
        )

        try:
            await loading_message.edit_text(error_message)
        except Exception:
            await update.message.reply_text(error_message)