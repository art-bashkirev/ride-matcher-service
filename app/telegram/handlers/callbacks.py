"""Callback query handlers for inline keyboards."""
from datetime import datetime, timedelta
from typing import Tuple

from telegram import Update, InlineKeyboardMarkup
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


async def _fetch_and_format_schedule(station_id: str, page: int = 1) -> Tuple[str, InlineKeyboardMarkup]:
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
    
    now_local = datetime.now(config.timezone)
    today = now_local.strftime('%Y-%m-%d')

    base_request = ScheduleRequest(
        station=station_id,
        date=today,
        result_timezone=config.result_timezone,
        limit=500
    )

    requests = [base_request]
    if now_local.hour >= config.schedule_fetch_next_day_after_hour:
        tomorrow_date = (now_local + timedelta(days=1)).strftime('%Y-%m-%d')
        requests.append(base_request.model_copy(update={"date": tomorrow_date}))

    async with CachedYandexSchedules() as client:
        schedule_response, cache_flags, source_dates = await client.get_schedule_for_dates(requests)

    filtered_schedule = filter_upcoming_departures(
        schedule_response.schedule,
        current_time=now_local,
        window_hours=config.schedule_future_window_hours
    )
    
    # Paginate the results
    paginated_items, current_page, total_pages = paginate_schedule(filtered_schedule, page)
    
    if not paginated_items:
        error_message = f"📅 No upcoming departures found for station {station_id} on {today}" if page == 1 else f"📅 No departures found for station {station_id} on {today}"
        raise ValueError(error_message)
    
    # Format the response
    reply_text = format_schedule_reply(station_id, today, paginated_items, current_page, total_pages)
    
    # Add data source information for transparency
    all_cached = all(cache_flags)
    any_cached = any(cache_flags)
    if all_cached:
        data_source = "💾 Data from cache"
    elif any_cached:
        data_source = "💾/🌐 Mixed cache & API"
    else:
        data_source = "🌐 Fresh data from API"
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
    
    return final_text, keyboard


async def handle_schedule_from_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            await query.edit_message_text("❌ Invalid station ID format")
            return

        # Show loading state
        await query.edit_message_text("⏳ Loading schedule...")

        # Use shared function to fetch and format schedule
        final_text, keyboard = await _fetch_and_format_schedule(station_id, page=1)

        # Edit the message with schedule content
        await query.edit_message_text(final_text, reply_markup=keyboard)

        username = update.effective_user.username if update.effective_user else "unknown"
        logger.info("User %s requested schedule for station %s from search", username, station_id)

    except ValueError as e:
        # Handle no departures case
        await query.edit_message_text(str(e))
    except Exception as e:
        logger.error("Error handling schedule from search: %s", str(e))
        await query.edit_message_text("❌ Error loading schedule. Please try again.")


async def handle_schedule_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            await query.edit_message_text("❌ Invalid station ID format")
            return

        # Show loading state
        await query.edit_message_text("⏳ Loading page...")

        # Use shared function to fetch and format schedule
        final_text, keyboard = await _fetch_and_format_schedule(station_id, page)

        # Edit the message with new content
        await query.edit_message_text(final_text, reply_markup=keyboard)

        username = update.effective_user.username if update.effective_user else "unknown"
        logger.info("User %s navigated to page %d for station %s", username, page, station_id)

    except ValueError as e:
        # Handle invalid page number or no departures
        if "Invalid page number" in str(e):
            await query.edit_message_text("❌ Invalid page number")
        else:
            await query.edit_message_text(str(e))
    except Exception as e:
        logger.error("Error handling schedule pagination: %s", str(e))
        await query.edit_message_text("❌ Error loading schedule page. Please try again.")


async def handle_noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle no-operation callbacks (like page indicator buttons)."""
    query = update.callback_query
    if query:
        await query.answer()  # Just acknowledge, do nothing
