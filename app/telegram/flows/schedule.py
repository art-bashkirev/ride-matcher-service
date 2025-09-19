from datetime import date, timedelta
from typing import List
from pydantic import BaseModel
from telegram import Update
from telegram.ext import ContextTypes
from services.cache import CacheService
from services.yandex_schedules.client import YandexSchedules
from services.yandex_schedules.models.schedule import ScheduleRequest, Schedule

class CachedScheduleList(BaseModel):
    schedules: List[Schedule]

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if context.args:
        station_id = context.args[0]
    else:
        await update.message.reply_text("Please provide a station id after the command, e.g. /schedule 12345")
        return
    
    # Get schedules for today and tomorrow
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    # Fetch today's schedule
    cached_today = CacheService.get_cached_model(station_id, today.isoformat(), CachedScheduleList, "ScheduleList")
    if cached_today:
        sched_today = cached_today.schedules
    else:
        async with YandexSchedules() as api:
            req = ScheduleRequest(station=station_id, date=today.isoformat())
            response = await api.get_schedule(req)
            sched_today = response.schedule
            CacheService.set_cached_model(station_id, today.isoformat(), CachedScheduleList(schedules=sched_today), model_name="ScheduleList")
    
    # Fetch tomorrow's schedule
    cached_tomorrow = CacheService.get_cached_model(station_id, tomorrow.isoformat(), CachedScheduleList, "ScheduleList")
    if cached_tomorrow:
        sched_tomorrow = cached_tomorrow.schedules
    else:
        async with YandexSchedules() as api:
            req = ScheduleRequest(station=station_id, date=tomorrow.isoformat())
            response = await api.get_schedule(req)
            sched_tomorrow = response.schedule
            CacheService.set_cached_model(station_id, tomorrow.isoformat(), CachedScheduleList(schedules=sched_tomorrow), model_name="ScheduleList")
    
    # Combine schedules
    combined_sched = sched_today + sched_tomorrow
    
    # Format the schedule
    if not combined_sched:
        formatted = "No schedule available."
    else:
        formatted_lines = []
        for item in combined_sched:
            departure = item.departure or "Unknown"
            thread_title = item.thread.title if item.thread else "Unknown"
            formatted_lines.append(f"{departure}: {thread_title}")
        formatted = "\n".join(formatted_lines)
    
    await update.message.reply_text("Schedule for today and tomorrow:\n" + formatted)
