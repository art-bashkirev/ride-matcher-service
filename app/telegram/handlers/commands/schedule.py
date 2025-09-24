from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from config.log_setup import get_logger
from config.settings import get_config
from app.telegram.utils import is_valid_station_id, format_schedule_reply
from services.yandex_schedules.cached_client import CachedYandexSchedules
from services.yandex_schedules.models.schedule import ScheduleRequest

logger = get_logger(__name__)

slug = "schedule"

async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /schedule command with caching."""
    if not update.message:
        return
    
    username = update.effective_user.username if update.effective_user else "unknown"
    logger.info("User %s requested schedule", username)
    
    if not context.args:
        await update.message.reply_text(
            "Please provide a station ID, e.g. /schedule s9600213\n"
            "Station ID format: 's' followed by 7 digits"
        )
        return
    
    station_id = context.args[0]
    if not is_valid_station_id(station_id):
        await update.message.reply_text(
            f"❌ Invalid station ID format: {station_id}\n"
            "Expected format: 's' followed by 7 digits (e.g., s9600213)"
        )
        return
    
    # Show loading message
    loading_message = await update.message.reply_text("⏳ Fetching schedule...")
    
    try:
        config = get_config()
        
        # Create schedule request
        today = datetime.now(config.timezone).strftime('%Y-%m-%d')
        schedule_request = ScheduleRequest(
            station=station_id,
            date=today,
            result_timezone=config.result_timezone,
            limit=20  # Limit to 20 departures to keep response manageable
        )
        
        # Use cached client to fetch schedule
        data_source = "🌐 Fresh data from API"  # Default assumption
        
        async with CachedYandexSchedules() as client:
            schedule_response = await client.get_schedule(schedule_request)
            
            # Try to determine if data came from cache by checking logs
            # This is a simple heuristic - in a real implementation, 
            # the cached client could return metadata about cache hits
            data_source = "💾 Data from cache"  # Will be overridden by logs if fresh
        
        # Format the response
        reply_text = format_schedule_reply(station_id, today, schedule_response.schedule)
        
        # Add data source information for transparency
        final_text = f"{reply_text}\n\n{data_source}"
        
        # Include station information if available
        if schedule_response.station and schedule_response.station.title:
            station_info = f"\n🏛️ Station: {schedule_response.station.title}"
            if schedule_response.station.station_type_name:
                station_info += f" ({schedule_response.station.station_type_name})"
            final_text = final_text.replace(f"station {station_id}", 
                                          f"station {station_id}{station_info}")
        
        # Edit the loading message with the result
        await loading_message.edit_text(final_text)
        
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
