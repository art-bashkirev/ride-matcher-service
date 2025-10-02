"""Callback query handlers for inline keyboards."""

from datetime import datetime
from typing import Tuple

from telegram import Update, InlineKeyboardMarkup
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
from services.yandex_schedules.models.schedule import ScheduleRequest, ScheduleResponse

logger = get_logger(__name__)


async def _fetch_and_format_schedule(
    station_id: str, page: int = 1
) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Common function to fetch schedule data and format it for display.

    Args:
        station_id: The station ID to fetch schedule for
        page: Page number for pagination (default: 1)

    Returns:
        Tuple of (formatted_text, keyboard) for the response

    Raises:
        Exception: If schedule cannot be fetched or formatted
    """
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

    schedule_items = schedule_response.schedule or []
    filtered_schedule = filter_upcoming_departures(schedule_items)

    paginated_items, current_page, total_pages = paginate_schedule(
        filtered_schedule, page
    )

    if not paginated_items:
        if page == 1:
            error_message = get_message(
                "schedule_no_upcoming_departures", station_id=station_id, date=today
            )
        else:
            error_message = get_message(
                "schedule_no_departures_generic", station_id=station_id, date=today
            )
        raise ValueError(error_message)

    reply_text = format_schedule_reply(
        station_id, today, paginated_items, current_page, total_pages
    )

    data_source = (
        get_message("schedule_data_source_cache")
        if was_cached
        else get_message("schedule_data_source_api")
    )
    final_text = f"{reply_text}\n\n{data_source}"

    if schedule_response.station and schedule_response.station.title:
        station_type_suffix = ""
        if schedule_response.station.station_type_name:
            station_type_suffix = f" ({schedule_response.station.station_type_name})"
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

    return final_text, keyboard


async def handle_schedule_from_search(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle schedule callback queries from search results."""
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()  # Acknowledge the callback

    try:
        # Parse callback data: "schedule_station_code"
        if not query.data.startswith("schedule_"):
            return

        station_id = query.data[9:]  # Remove "schedule_" prefix

        if not is_valid_station_id(station_id):
            await query.edit_message_text(get_message("schedule_invalid_station_id"))
            return

        # Show loading state
        await query.edit_message_text(get_message("schedule_loading_schedule"))

        # Use shared function to fetch and format schedule
        final_text, keyboard = await _fetch_and_format_schedule(station_id, page=1)

        # Edit the message with schedule content
        await query.edit_message_text(final_text, reply_markup=keyboard)

        username = (
            update.effective_user.username if update.effective_user else "unknown"
        )
        logger.info(
            "User %s requested schedule for station %s from search",
            username,
            station_id,
        )

    except ValueError as e:
        # Handle no departures case
        await query.edit_message_text(str(e))
    except Exception as e:
        logger.error("Error handling schedule from search: %s", str(e))
        await query.edit_message_text(get_message("schedule_error_loading_schedule"))


async def handle_schedule_pagination(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle pagination callback queries for schedule."""
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()  # Acknowledge the callback

    try:
        # Parse callback data: "schedule_page:station_id:page"
        parts = query.data.split(":")
        if len(parts) != 3 or parts[0] != "schedule_page":
            return

        station_id = parts[1]
        page = int(parts[2])

        if not is_valid_station_id(station_id):
            await query.edit_message_text(get_message("schedule_invalid_station_id"))
            return

        # Show loading state
        await query.edit_message_text(get_message("schedule_loading_page"))

        # Use shared function to fetch and format schedule
        final_text, keyboard = await _fetch_and_format_schedule(station_id, page)

        # Edit the message with new content
        await query.edit_message_text(final_text, reply_markup=keyboard)

        username = (
            update.effective_user.username if update.effective_user else "unknown"
        )
        logger.info(
            "User %s navigated to page %d for station %s", username, page, station_id
        )

    except ValueError as e:
        # Handle invalid page number or no departures
        if "Invalid page number" in str(e):
            await query.edit_message_text(get_message("schedule_invalid_page_number"))
        else:
            await query.edit_message_text(str(e))
    except Exception as e:
        logger.error("Error handling schedule pagination: %s", str(e))
        await query.edit_message_text(get_message("schedule_error_loading_page"))


async def handle_noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle no-operation callbacks (like page indicator buttons)."""
    query = update.callback_query
    if query:
        await query.answer()  # Just acknowledge, do nothing
