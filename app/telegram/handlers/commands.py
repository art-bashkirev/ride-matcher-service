from __future__ import annotations
import re
from datetime import datetime
from telegram import Update, ForceReply
from telegram.ext import ContextTypes

from config.settings import get_config
from services.yandex_schedules.client import YandexSchedules
from services.yandex_schedules.models.schedule import ScheduleRequest

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
    
    # Validate message format: s followed by exactly 7 digits
    pattern = r'^s\d{7}$'
    if re.match(pattern, message_text):
        # Extract station ID
        station_id = message_text
        
        try:
            # Get configuration
            config = get_config()
            
            # Create Yandex Schedules client
            async with YandexSchedules() as client:
                # Create schedule request
                today = datetime.now().date().isoformat()
                schedule_request = ScheduleRequest(
                    station=station_id,
                    date=today,
                    result_timezone=config.result_timezone
                )
                
                # Get schedule
                response = await client.get_schedule(schedule_request)
                
                # Format response
                if response.schedule:
                    reply_text = f"📅 Schedule for station {station_id} on {today}:\n\n"
                    for schedule_item in response.schedule[:5]:  # Limit to first 5 items
                        departure = schedule_item.departure or "N/A"
                        thread_title = schedule_item.thread.title if schedule_item.thread else "N/A"
                        reply_text += f"🚂 {thread_title}\n"
                        reply_text += f"🕒 Departure: {departure}\n"
                        if schedule_item.arrival:
                            reply_text += f"🕒 Arrival: {schedule_item.arrival}\n"
                        reply_text += "\n"
                    
                    if len(response.schedule) > 5:
                        reply_text += f"... and {len(response.schedule) - 5} more departures"
                else:
                    reply_text = f"No schedule found for station {station_id} on {today}"
                
        except Exception as e:
            reply_text = f"Error fetching schedule: {str(e)}"
    else:
        reply_text = f"Invalid format. Please send a station ID in format 's1234567' (s followed by 7 digits)."
    
    await update.message.reply_text(reply_text)

__all__ = ["cmd_start", "cmd_help", "echo_text"]
