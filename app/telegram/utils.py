import re
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from services.yandex_schedules.models.schedule import Schedule

ISO_UTC_SUFFIX = "+00:00"


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', ISO_UTC_SUFFIX))
    except (ValueError, AttributeError):
        return None


@dataclass(frozen=True)
class ScheduleDisplayItem:
    schedule: Schedule
    departure_dt: Optional[datetime]
    arrival_dt: Optional[datetime]
    is_next_day: bool


def _align_datetime(value: Optional[datetime], target_tz) -> Optional[datetime]:
    if value is None or target_tz is None:
        return value
    if value.tzinfo is None:
        return value.replace(tzinfo=target_tz)
    return value.astimezone(target_tz)


def _should_include_departure(
        departure: Optional[datetime],
        current_time: datetime,
        cutoff_time: Optional[datetime]
) -> tuple[bool, bool]:
    aligned_departure = _align_datetime(departure, current_time.tzinfo)

    if aligned_departure is None:
        return True, False

    if aligned_departure <= current_time:
        return False, False

    if cutoff_time and aligned_departure > cutoff_time:
        return False, False

    return True, aligned_departure.date() > current_time.date()


def is_valid_station_id(text: str) -> bool:
    """Validate message format: s followed by exactly 7 digits."""
    return bool(re.match(r'^s\d{7}$', text))


def filter_upcoming_departures(
    schedule: List[Schedule],
    current_time: Optional[datetime] = None,
    *,
    window_hours: Optional[int] = None
) -> List[ScheduleDisplayItem]:
    """Filter schedule to show only upcoming departures.
    
    Args:
        schedule: List of schedule items
        current_time: Current time (defaults to now in UTC)
        window_hours: Optional number of hours ahead to include (hard cutoff)
    
    Returns:
        List of upcoming schedule items (not limited here, display limiting handled by caller)
    """
    if not schedule:
        return []

    if current_time is None:
        current_time = datetime.now(timezone.utc)

    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    cutoff_time = current_time + timedelta(hours=window_hours) if window_hours is not None else None

    upcoming: List[ScheduleDisplayItem] = []
    for item in schedule:
        departure_dt = _parse_iso_datetime(item.departure)
        arrival_dt = _parse_iso_datetime(item.arrival)

        include, is_next_day = _should_include_departure(departure_dt, current_time, cutoff_time)

        if not include:
            continue

        display_departure = _align_datetime(departure_dt, current_time.tzinfo)
        display_arrival = _align_datetime(arrival_dt, current_time.tzinfo)

        upcoming.append(ScheduleDisplayItem(item, display_departure, display_arrival, is_next_day))

    # Return all upcoming departures without artificial limit
    # Display limiting is handled by the caller (format_schedule_reply)
    return upcoming


def format_schedule_reply(station_id: str, date: str, schedule: List[ScheduleDisplayItem], current_page: int = 1,
                          total_pages: int = 1) -> str:
    """Format schedule data for telegram response."""
    if not schedule:
        return f"📅 No departures found for station {station_id} on {date}"

    station_name = _extract_station_display_name(schedule)
    page_info = f" (Page {current_page}/{total_pages})" if total_pages > 1 else ""
    header = f"📅 Schedule for station {station_id}{station_name} on {date}{page_info}:"

    body_lines: List[str] = []
    for entry in schedule:
        body_lines.extend(_format_schedule_entry(entry))

    body_text = "\n".join(line for line in body_lines if line).strip()
    if body_text:
        return f"{header}\n\n{body_text}"
    return header


def _extract_station_display_name(schedule: List[ScheduleDisplayItem]) -> str:
    if not schedule:
        return ""

    thread = schedule[0].schedule.thread
    if thread and thread.title:
        parts = thread.title.split(" - ")
        if len(parts) >= 2:
            return f" ({parts[0]})"
    return ""


def _format_schedule_entry(entry: ScheduleDisplayItem) -> List[str]:
    schedule_item = entry.schedule
    lines = [f"🚂 {_format_thread_info(schedule_item)}"]

    time_line = f"🕒 {_format_time_info(entry)}{_format_platform_info(schedule_item)}"
    lines.append(time_line)

    if schedule_item.stops and len(schedule_item.stops) < 50:
        lines.append(f"📍 Stops: {schedule_item.stops}")

    lines.append("")
    return lines


def _format_thread_info(schedule_item: Schedule) -> str:
    thread = schedule_item.thread
    if not thread:
        return "Unknown"

    if thread.number:
        info = thread.number
        if thread.title:
            info += f" ({thread.title})"
        return info

    return thread.title or "Unknown"


def _format_time_info(entry: ScheduleDisplayItem) -> str:
    schedule_item = entry.schedule

    if entry.arrival_dt and entry.departure_dt:
        arrival_time = entry.arrival_dt.strftime('%H:%M')
        departure_time = entry.departure_dt.strftime('%H:%M')
        base = f"Arrives: {arrival_time}, Departs: {departure_time}"
    elif entry.departure_dt:
        base = f"Departs: {entry.departure_dt.strftime('%H:%M')}"
    elif entry.arrival_dt:
        base = f"Arrives: {entry.arrival_dt.strftime('%H:%M')}"
    elif schedule_item.departure:
        base = f"Departs: {schedule_item.departure}"
    elif schedule_item.arrival:
        base = f"Arrives: {schedule_item.arrival}"
    else:
        base = "N/A"

    if entry.is_next_day:
        return f"{base} (next day)"
    return base


def _format_platform_info(schedule_item: Schedule) -> str:
    return f" (Platform {schedule_item.platform})" if schedule_item.platform else ""


def create_pagination_keyboard(station_id: str, current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Create pagination keyboard for schedule navigation."""
    keyboard = []

    if total_pages <= 1:
        return InlineKeyboardMarkup(keyboard)

    buttons = []

    # Previous button
    if current_page > 1:
        prev_callback = f"schedule_page:{station_id}:{current_page - 1}"
        buttons.append(InlineKeyboardButton("◀️ Previous", callback_data=prev_callback))

    # Page indicator
    page_indicator = f"Page {current_page}/{total_pages}"
    buttons.append(InlineKeyboardButton(page_indicator, callback_data="noop"))

    # Next button  
    if current_page < total_pages:
        next_callback = f"schedule_page:{station_id}:{current_page + 1}"
        buttons.append(InlineKeyboardButton("Next ▶️", callback_data=next_callback))

    keyboard.append(buttons)
    return InlineKeyboardMarkup(keyboard)


def paginate_schedule(schedule: List[ScheduleDisplayItem], page: int = 1, per_page: int = 10) -> Tuple[List[ScheduleDisplayItem], int, int]:
    """Paginate schedule results.
    
    Args:
        schedule: List of schedule items
        page: Current page number (1-based)
        per_page: Items per page
        
    Returns:
        Tuple of (paginated_items, current_page, total_pages)
    """
    if not schedule:
        return [], 1, 1

    total_items = len(schedule)
    total_pages = max(1, (total_items + per_page - 1) // per_page)  # Ceiling division
    current_page = max(1, min(page, total_pages))  # Clamp to valid range

    start_index = (current_page - 1) * per_page
    end_index = min(start_index + per_page, total_items)

    paginated_items = schedule[start_index:end_index]

    return paginated_items, current_page, total_pages
