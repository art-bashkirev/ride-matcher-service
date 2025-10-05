from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from app.telegram.utils import (
    is_valid_station_id,
    format_schedule_reply,
    filter_upcoming_departures,
    paginate_schedule,
    create_pagination_keyboard,
)
from app.telegram.messages import get_message
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

    user = update.effective_user
    telegram_id = getattr(user, "id", None) if user else None
    username = user.username if user else "unknown"

    if not context.args:
        # Use messages for error messages
        help_title = get_message("schedule_cmd_help_title")
        missing_id = get_message("schedule_cmd_missing_id")
        usage = get_message("schedule_cmd_usage")
        format_info = get_message("schedule_cmd_format")
        tip = get_message("schedule_cmd_tip")
        separator = get_message("separator")

        await update.message.reply_text(
            f"{help_title}\n"
            f"{separator}\n\n"
            f"{missing_id}\n\n"
            f"{usage}\n\n"
            f"{format_info}\n\n"
            f"{tip}"
        )
        logger.info("User %s requested schedule without arguments", username)
        return

    station_id = context.args[0]
    if not is_valid_station_id(station_id):
        # Use messages for error messages
        error_title = get_message("schedule_error_invalid_format")
        you_entered = get_message("schedule_error_you_entered", station_id=station_id)
        expected_format = get_message("schedule_error_expected_format")
        try_again = get_message("schedule_error_try_again")
        separator = get_message("separator")

        await update.message.reply_text(
            f"{error_title}\n"
            f"{separator}\n\n"
            f"{you_entered}\n\n"
            f"{expected_format}\n\n"
            f"{try_again}"
        )
        logger.info("User %s requested schedule with parsing error", username)
        return

    # Show loading message
    loading_message = await update.message.reply_text(get_message("loading"))

    logger.info("Trying to serve schedule to User %s ", username)

    try:
        config = get_config()

        # Create schedule request - fetch many trains to cache and filter
        today = datetime.now(config.timezone).strftime("%Y-%m-%d")
        schedule_request = ScheduleRequest(
            station=station_id,
            date=today,
            result_timezone=config.result_timezone,
            limit=500,  # Fetch many trains to cache properly and filter current ones
        )

        # Use cached client to fetch schedule
        async with CachedYandexSchedules() as client:
            schedule_response, was_cached = await client.get_schedule(schedule_request)

            # Set data source based on actual cache hit
            data_source = (
                get_message("schedule_data_source_cache")
                if was_cached
                else get_message("schedule_data_source_api")
            )

        # Filter to show only upcoming departures from the large cached set
        schedule_items = schedule_response.schedule or []
        filtered_schedule = filter_upcoming_departures(schedule_items)

        # Paginate the results (page 1 by default)
        paginated_items, current_page, total_pages = paginate_schedule(
            filtered_schedule, page=1
        )

        if not paginated_items:
            error_message = format_schedule_reply(station_id, today, [], 1, 1)
            await loading_message.edit_text(error_message)
            return

        # Format the response
        reply_text = format_schedule_reply(
            station_id, today, paginated_items, current_page, total_pages
        )

        # Add data source information for transparency
        final_text = f"{reply_text}\n\n{data_source}"

        # Include station information if available
        if schedule_response.station and schedule_response.station.title:
            station_type_suffix = ""
            if schedule_response.station.station_type_name:
                # Escape parentheses for MarkdownV2
                station_type_suffix = (
                    f" \\({schedule_response.station.station_type_name}\\)"
                )
            station_info = get_message(
                "schedule_station_info",
                title=schedule_response.station.title,
                station_type=station_type_suffix,
            )
            final_text = final_text.replace(
                f"station {station_id}", f"station {station_id}{station_info}"
            )

        # Create pagination keyboard
        keyboard = create_pagination_keyboard(station_id, current_page, total_pages)

        # Edit the loading message with the result
        await loading_message.edit_text(final_text, reply_markup=keyboard)

        logger.info(
            "Successfully served schedule for station %s to user %s",
            station_id,
            username,
        )

    except Exception as e:
        logger.error("Error fetching schedule for station %s: %s", station_id, str(e))
        error_msg = get_message("error_generic")

        try:
            await loading_message.edit_text(error_msg)
        except Exception:
            await update.message.reply_text(error_msg)
