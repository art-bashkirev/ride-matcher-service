from __future__ import annotations
from datetime import datetime
from telegram import Update, ForceReply
from telegram.ext import ContextTypes

from config.settings import get_config
from config.log_setup import get_logger
from services.yandex_schedules.client import YandexSchedules
from services.yandex_schedules.models.schedule import ScheduleRequest, ScheduleResponse
from services.cache import CacheService
from app.telegram.utils import is_valid_station_id, format_schedule_reply
from services.yandex_schedules.models.schedule import ScheduleRequest, Schedule
from services.cache import CacheService
from app.telegram.utils import is_valid_station_id, format_schedule_reply

logger = get_logger(__name__)

def filter_future_departures(schedule: list[Schedule]) -> list[Schedule]:
    """Filter schedule to only include departures after current time."""
    now = datetime.now()
    filtered = []
    for item in schedule:
        if item.departure:
            try:
                departure_dt = datetime.fromisoformat(item.departure)
                # If departure has timezone, make now timezone-aware
                if departure_dt.tzinfo:
                    now = datetime.now(departure_dt.tzinfo)
                if departure_dt > now:
                    filtered.append(item)
            except ValueError:
                # If parsing fails, include it anyway
                filtered.append(item)
        else:
            # If no departure time, include it
            filtered.append(item)
    return filtered

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    user = update.effective_user
    mention = user.mention_html() if user else "there"
    logger.info("User %s started the bot", user.username if user else "unknown")
    await update.message.reply_html(rf"Hi {mention}!", reply_markup=ForceReply(selective=True))

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        logger.info("User %s requested help", update.effective_user.username if update.effective_user else "unknown")
        await update.message.reply_text("Help!")

async def echo_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    message_text = update.message.text.strip()
    user = update.effective_user
    logger.info("Received message from user %s: %s", user.username if user else "unknown", message_text)
    reply_text = ""

    if not is_valid_station_id(message_text):
        logger.warning("Invalid station ID format: %s", message_text)
        reply_text = (
            "Invalid format. Please send a station ID in format 's1234567' (s followed by 7 digits)."
        )
    else:
        station_id = message_text
        today = datetime.now().date().isoformat()
        try:
            # Check cache first
            cached_response = CacheService.get_cached_model(station_id, today, ScheduleResponse)
            if cached_response:
                logger.info("Cache hit for station %s on %s", station_id, today)
                filtered_schedule = filter_future_departures(cached_response.schedule)
                reply_text = format_schedule_reply(station_id, today, filtered_schedule) + " (from cache)"
            else:
                logger.info("Cache miss for station %s on %s, fetching from API", station_id, today)
                # Cache miss - fetch from API
                config = get_config()
                async with YandexSchedules() as client:
                    schedule_request = ScheduleRequest(
                        station=station_id,
                        date=today,
                        result_timezone=config.result_timezone
                    )
                    response = await client.get_schedule(schedule_request)
                    
                    # Filter departures to only show those after current time
                    filtered_schedule = filter_future_departures(response.schedule)
                    
                    # Cache the full response (unfiltered for future use)
                    CacheService.set_cached_model(
                        station_id, 
                        today, 
                        response,
                        ttl_hours=1
                    )
                    
                    reply_text = format_schedule_reply(station_id, today, filtered_schedule) + " (fetched fresh)"
        except Exception as e:
            logger.error("Error fetching schedule for station %s: %s", station_id, str(e))
            reply_text = f"Error fetching schedule: {str(e)}"

    await update.message.reply_text(reply_text)
