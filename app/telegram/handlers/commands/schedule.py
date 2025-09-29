from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from app.telegram.utils import (
    is_valid_station_id,
    format_schedule_reply,
    filter_upcoming_departures,
    paginate_schedule,
    create_pagination_keyboard
)
from config.log_setup import get_logger
from config.settings import get_config
from services.yandex_schedules.cached_client import CachedYandexSchedules
from services.yandex_schedules.models.schedule import ScheduleRequest

logger = get_logger(__name__)

slug = "schedule"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /schedule command with caching."""
    if not update.message:
        return

    username = update.effective_user.username if update.effective_user else "unknown"

    if not context.args:
        await update.message.reply_text(
            "🚂 **Schedule Command Help**\n"
            "══════════════════════════\n\n"
            "❓ **Missing Station ID**\n\n"
            "📋 **Usage:**\n"
            "`/schedule s9600213`\n\n"
            "📝 **Format:**\n"
            "• Station ID: 's' + 7 digits\n"
            "• Example: s9600213\n\n"
            "💡 **Tip:** Use /setstations to configure your stations first!"
        )
        logger.info("User %s requested schedule without arguments", username)
        return

    station_id = context.args[0]
    if not is_valid_station_id(station_id):
        await update.message.reply_text(
            f"❌ **Invalid Station ID Format**\n"
            f"═══════════════════════════════\n\n"
            f"🔍 **You entered:** `{station_id}`\n\n"
            f"✅ **Expected format:**\n"
            f"• 's' followed by exactly 7 digits\n"
            f"• Example: s9600213\n\n"
            f"💡 **Try again with correct format!**"
        )
        logger.info("User %s requested schedule with parsing error", username)
        return

    # Show loading message
    loading_message = await update.message.reply_text("⏳ **Fetching schedule data...**\n\n🔄 Please wait while I get the latest information...")

    logger.info("Trying to serve schedule to User %s ", username)

    try:
        config = get_config()

        # Create schedule request - fetch many trains to cache and filter
        today = datetime.now(config.timezone).strftime('%Y-%m-%d')
        schedule_request = ScheduleRequest(
            station=station_id,
            date=today,
            result_timezone=config.result_timezone,
            limit=500  # Fetch many trains to cache properly and filter current ones
        )

        # Use cached client to fetch schedule
        async with CachedYandexSchedules() as client:
            schedule_response, was_cached = await client.get_schedule(schedule_request)

            # Set data source based on actual cache hit
            data_source = "💾 Data from cache" if was_cached else "🌐 Fresh data from API"

        # Filter to show only upcoming departures from the large cached set
        filtered_schedule = filter_upcoming_departures(schedule_response.schedule)

        # Paginate the results (page 1 by default)
        paginated_items, current_page, total_pages = paginate_schedule(filtered_schedule, page=1)

        if not paginated_items:
            error_message = f"📅 No upcoming departures found for station {station_id} on {today}"
            await loading_message.edit_text(error_message)
            return

        # Format the response
        reply_text = format_schedule_reply(station_id, today, paginated_items, current_page, total_pages)

        # Add data source information for transparency
        final_text = f"{reply_text}\n\n{data_source}"

        # Include station information if available
        if schedule_response.station and schedule_response.station.title:
            station_info = f"\n🏛️ Station: {schedule_response.station.title}"
            if schedule_response.station.station_type_name:
                station_info += f" ({schedule_response.station.station_type_name})"
            final_text = final_text.replace(f"station {station_id}",
                                            f"station {station_id}{station_info}")

        # Create pagination keyboard
        keyboard = create_pagination_keyboard(station_id, current_page, total_pages)

        # Edit the loading message with the result
        await loading_message.edit_text(final_text, reply_markup=keyboard)

        logger.info("Successfully served schedule for station %s to user %s",
                    station_id, username)

    except Exception as e:
        logger.error("Error fetching schedule for station %s: %s", station_id, str(e))

        error_message = (
            f"❌ Error fetching schedule for station {station_id}\n"
            f"Please check if the station ID is correct and try again later."
        )

        try:
            await loading_message.edit_text(error_message)
        except Exception:
            await update.message.reply_text(error_message)
