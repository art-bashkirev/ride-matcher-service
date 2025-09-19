import re
from datetime import datetime

def is_valid_station_id(text: str) -> bool:
    """Validate message format: s followed by exactly 7 digits."""
    return bool(re.match(r'^s\d{7}$', text))

def format_schedule_reply(station_id: str, today: str, schedule) -> str:
    if not schedule:
        return f"No schedule found for station {station_id} on {today}"
    reply_text = f"📅 Schedule for station {station_id} on {today}:\n\n"
    for schedule_item in schedule[:10]:  # Limit to first 10 items
        departure = schedule_item.departure or "N/A"
        thread_title = schedule_item.thread.title if schedule_item.thread else "N/A"
        reply_text += f"🚂 {thread_title}\n"
        reply_text += f"🕒 Departure: {departure}\n"
        if schedule_item.arrival:
            reply_text += f"🕒 Arrival: {schedule_item.arrival}\n"
        reply_text += "\n"
    if len(schedule) > 10:
        reply_text += f"... and {len(schedule) - 10} more departures"
    return reply_text