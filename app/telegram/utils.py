import re
from datetime import datetime, timezone
from typing import List, Optional
from services.yandex_schedules.models.schedule import Schedule

def is_valid_station_id(text: str) -> bool:
    """Validate message format: s followed by exactly 7 digits."""
    return bool(re.match(r'^s\d{7}$', text))

def filter_upcoming_departures(schedule: List[Schedule], current_time: Optional[datetime] = None) -> List[Schedule]:
    """Filter schedule to show only upcoming departures.
    
    Args:
        schedule: List of schedule items
        current_time: Current time (defaults to now in UTC)
    
    Returns:
        List of upcoming schedule items (not limited here, display limiting handled by caller)
    """
    if not schedule:
        return []
    
    if current_time is None:
        current_time = datetime.now(timezone.utc)
    
    upcoming = []
    for item in schedule:
        if item.departure:
            try:
                # Parse ISO 8601 datetime with timezone
                departure_dt = datetime.fromisoformat(item.departure.replace('Z', '+00:00'))
                
                # Compare with current time
                if departure_dt > current_time:
                    upcoming.append(item)
            except (ValueError, AttributeError):
                # If we can't parse the time, include it to be safe
                upcoming.append(item)
    
    # Return all upcoming departures without artificial limit
    # Display limiting is handled by the caller (format_schedule_reply)
    return upcoming

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
        # Format time information for this station
        time_info = ""
        if schedule_item.arrival and schedule_item.departure:
            try:
                arrival_dt = datetime.fromisoformat(schedule_item.arrival.replace('Z', '+00:00'))
                departure_dt = datetime.fromisoformat(schedule_item.departure.replace('Z', '+00:00'))
                arrival_time = arrival_dt.strftime('%H:%M')
                departure_time = departure_dt.strftime('%H:%M')
                time_info = f"Arrives: {arrival_time}, Departs: {departure_time}"
            except (ValueError, AttributeError):
                time_info = f"Arrives: {schedule_item.arrival}, Departs: {schedule_item.departure}"
        elif schedule_item.departure:
            try:
                dt = datetime.fromisoformat(schedule_item.departure.replace('Z', '+00:00'))
                departure_time = dt.strftime('%H:%M')
                time_info = f"Departs: {departure_time}"
            except (ValueError, AttributeError):
                time_info = f"Departs: {schedule_item.departure}"
        elif schedule_item.arrival:
            try:
                dt = datetime.fromisoformat(schedule_item.arrival.replace('Z', '+00:00'))
                arrival_time = dt.strftime('%H:%M')
                time_info = f"Arrives: {arrival_time}"
            except (ValueError, AttributeError):
                time_info = f"Arrives: {schedule_item.arrival}"
        else:
            time_info = "N/A"
        
        # Get thread information
        thread_info = "Unknown"
        if schedule_item.thread:
            # Prefer number over title for trains, but show title for others
            if schedule_item.thread.number:
                thread_info = f"{schedule_item.thread.number}"
                if schedule_item.thread.title:
                    # Add full title without shortening
                    thread_info += f" ({schedule_item.thread.title})"
            else:
                thread_info = schedule_item.thread.title or "Unknown"
        
        # Format platform information
        platform_info = ""
        if schedule_item.platform:
            platform_info = f" (Platform {schedule_item.platform})"
        
        reply_text += f"🚂 {thread_info}\n"
        reply_text += f"🕒 {time_info}{platform_info}\n"
        
        # Add stops information if available and not too long
        if schedule_item.stops and len(schedule_item.stops) < 50:
            reply_text += f"📍 Stops: {schedule_item.stops}\n"
        
        reply_text += "\n"
    
    if len(schedule) > 10:
        reply_text += f"... and {len(schedule) - 10} more departures\n"
    
    return reply_text.strip()