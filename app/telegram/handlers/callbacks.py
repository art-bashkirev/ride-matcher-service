"""Callback query handlers for inline keyboards."""
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from config.log_setup import get_logger
from config.settings import get_config
from app.telegram.utils import (
    is_valid_station_id, 
    format_schedule_reply, 
    filter_upcoming_departures,
    paginate_schedule,
    create_pagination_keyboard
)
from services.yandex_schedules.cached_client import CachedYandexSchedules
from services.yandex_schedules.models.schedule import ScheduleRequest

logger = get_logger(__name__)

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
        
        # Filter to show only upcoming departures from the large cached set
        filtered_schedule = filter_upcoming_departures(schedule_response.schedule)
        
        # Paginate the results
        paginated_items, current_page, total_pages = paginate_schedule(filtered_schedule, page)
        
        if not paginated_items:
            await query.edit_message_text(f"📅 No departures found for station {station_id} on {today}")
            return
        
        # Format the response with pagination info
        reply_text = format_schedule_reply(station_id, today, paginated_items, current_page, total_pages)
        
        # Add data source information for transparency
        data_source = "💾 Data from cache" if was_cached else "🌐 Fresh data from API"
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
        
        # Edit the message with new content
        await query.edit_message_text(final_text, reply_markup=keyboard)
        
        username = update.effective_user.username if update.effective_user else "unknown"
        logger.info("User %s navigated to page %d for station %s", username, current_page, station_id)
        
    except ValueError:
        await query.edit_message_text("❌ Invalid page number")
    except Exception as e:
        logger.error("Error handling schedule pagination: %s", str(e))
        await query.edit_message_text("❌ Error loading schedule page. Please try again.")

async def handle_noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle no-operation callbacks (like page indicator buttons)."""
    query = update.callback_query
    if query:
        await query.answer()  # Just acknowledge, do nothing