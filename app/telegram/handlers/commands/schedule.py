from datetime import datetime, timedelta

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
            "Please provide a station ID, e.g. /schedule s9600213\n"
            "Station ID format: 's' followed by 7 digits"
        )
        logger.info("User %s requested schedule without arguments", username)
        return

    station_id = context.args[0]
    if not is_valid_station_id(station_id):
        await update.message.reply_text(
            f"❌ Invalid station ID format: {station_id}\n"
            "Expected format: 's' followed by 7 digits (e.g., s9600213)"
        )
        logger.info("User %s requested schedule with parsing error", username)
        return

    # Show loading message
    loading_message = await update.message.reply_text("⏳ Fetching schedule...")

    logger.info("Trying to serve schedule to User %s ", username)

    try:
        config = get_config()

        now_local = datetime.now(config.timezone)
        today = now_local.strftime('%Y-%m-%d')

        base_request = ScheduleRequest(
            station=station_id,
            date=today,
            result_timezone=config.result_timezone,
            limit=500  # Fetch many trains to cache properly and filter current ones
        )

        requests = [base_request]

        if now_local.hour >= config.schedule_fetch_next_day_after_hour:
            tomorrow_date = (now_local + timedelta(days=1)).strftime('%Y-%m-%d')
            requests.append(base_request.model_copy(update={"date": tomorrow_date}))

        async with CachedYandexSchedules() as client:
            schedule_response, cache_flags, source_dates = await client.get_schedule_for_dates(requests)

        all_cached = all(cache_flags)
        any_cached = any(cache_flags)
        if all_cached:
            data_source = "💾 Data from cache"
        elif any_cached:
            data_source = "💾/🌐 Mixed cache & API"
        else:
            data_source = "🌐 Fresh data from API"

        filtered_schedule = filter_upcoming_departures(
            schedule_response.schedule,
            current_time=now_local,
            window_hours=config.schedule_future_window_hours
        )

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

        if len(source_dates) > 1:
            final_text += f"\n🗓️ Combined dates: {', '.join(source_dates)}"

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
        logger.error("Error fetching schedule for station %s: %s (%s)", 
                    station_id, str(e) or "No error message", type(e).__name__)
        import traceback
        logger.error("Full traceback: %s", traceback.format_exc())

        error_message = (
            f"❌ Error fetching schedule for station {station_id}\n"
            f"Please check if the station ID is correct and try again later."
        )

        try:
            await loading_message.edit_text(error_message)
        except Exception:
            await update.message.reply_text(error_message)
