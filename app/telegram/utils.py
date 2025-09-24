import re
from datetime import datetime
from typing import List, Optional
from services.yandex_schedules.models.schedule import Schedule

def is_valid_station_id(text: str) -> bool:
    """Validate message format: s followed by exactly 7 digits."""
    return bool(re.match(r'^s\d{7}$', text))

def format_schedule_reply(station_id: str, date: str, schedule: List[Schedule]) -> str:
    """Format schedule data for telegram response."""
    if not schedule:
        return f"📅 No departures found for station {station_id} on {date}"
    
    # Get station name from first schedule item if available
    station_name = ""
    if schedule and schedule[0].thread and schedule[0].thread.title:
        # Try to extract station name from thread title or use station_id
        thread_title = schedule[0].thread.title
        # Thread titles are usually "From - To" format
        parts = thread_title.split(" - ")
        if len(parts) >= 2:
            station_name = f" ({parts[0]})"
    
    reply_text = f"📅 Schedule for station {station_id}{station_name} on {date}:\n\n"
    
    # Show up to 10 departures to keep response manageable
    for i, schedule_item in enumerate(schedule[:10]):
        departure_time = "N/A"
        arrival_time = ""
        
        if schedule_item.departure:
            try:
                # Parse ISO datetime and format to time only
                dt = datetime.fromisoformat(schedule_item.departure.replace('Z', '+00:00'))
                departure_time = dt.strftime('%H:%M')
            except (ValueError, AttributeError):
                departure_time = schedule_item.departure
        
        if schedule_item.arrival:
            try:
                dt = datetime.fromisoformat(schedule_item.arrival.replace('Z', '+00:00'))
                arrival_time = f" → {dt.strftime('%H:%M')}"
            except (ValueError, AttributeError):
                arrival_time = f" → {schedule_item.arrival}"
        
        # Get thread information
        thread_info = "Unknown"
        if schedule_item.thread:
            thread_info = schedule_item.thread.title or schedule_item.thread.number or "Unknown"
            # Limit thread info length
            if len(thread_info) > 30:
                thread_info = thread_info[:27] + "..."
        
        # Format platform information
        platform_info = ""
        if schedule_item.platform:
            platform_info = f" (Platform {schedule_item.platform})"
        
        reply_text += f"🚂 {thread_info}\n"
        reply_text += f"🕒 {departure_time}{arrival_time}{platform_info}\n"
        
        # Add stops information if available and not too long
        if schedule_item.stops and len(schedule_item.stops) < 50:
            reply_text += f"📍 Stops: {schedule_item.stops}\n"
        
        reply_text += "\n"
    
    if len(schedule) > 10:
        reply_text += f"... and {len(schedule) - 10} more departures\n"
    
    return reply_text.strip()