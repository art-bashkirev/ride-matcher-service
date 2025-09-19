from __future__ import annotations
from datetime import datetime
from telegram import Update, ForceReply
from telegram.ext import ContextTypes

from config.settings import get_config
from services.yandex_schedules.client import YandexSchedules
from services.yandex_schedules.models.schedule import ScheduleRequest
from services.cache import CacheService
from app.telegram.utils import is_valid_station_id, format_schedule_reply

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    user = update.effective_user
    mention = user.mention_html() if user else "there"
    await update.message.reply_html(rf"Hi {mention}!", reply_markup=ForceReply(selective=True))

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Help!")

async def echo_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    message_text = update.message.text.strip()
    reply_text = ""

    if not is_valid_station_id(message_text):
        reply_text = (
            "Invalid format. Please send a station ID in format 's1234567' (s followed by 7 digits)."
        )
    else:
        station_id = message_text
        today = datetime.now().date().isoformat()
        try:
            # Check cache first
            cached_response = CacheService.get_cached_schedule(station_id, today)
            if cached_response:
                reply_text = format_schedule_reply(station_id, today, cached_response['schedule'])
            else:
                # Cache miss - fetch from API
                config = get_config()
                async with YandexSchedules() as client:
                    schedule_request = ScheduleRequest(
                        station=station_id,
                        date=today,
                        result_timezone=config.result_timezone
                    )
                    response = await client.get_schedule(schedule_request)
                    
                    # Cache the response
                    CacheService.set_cached_schedule(
                        station_id, 
                        today, 
                        response.model_dump(),  # Convert to dict for JSON storage
                        ttl_hours=1
                    )
                    
                    reply_text = format_schedule_reply(station_id, today, response.schedule)
        except Exception as e:
            reply_text = f"Error fetching schedule: {str(e)}"

    await update.message.reply_text(reply_text)
