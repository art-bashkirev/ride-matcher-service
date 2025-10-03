from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from telegram import Update
from telegram.ext import ContextTypes

from app.telegram.messages import get_message
from config.log_setup import get_logger
from config.settings import get_config
from services.yandex_schedules.cached_client import CachedYandexSchedules
from services.yandex_schedules.models.search import Segment, SearchRequest

logger = get_logger(__name__)


@dataclass(slots=True)
class RouteSegment:
    departure: datetime
    arrival: datetime
    train_label: str


_MAX_RESULTS_TO_SHOW = 8
_PAST_DEPARTURE_GRACE_MINUTES = 5


def _escape_markdown(text: str) -> str:
    """Escape Telegram Markdown special characters for v1 format."""
    if not text:
        return ""

    return (
        text.replace("_", "\\_")
        .replace("*", "\\*")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("`", "\\`")
    )


def _format_station(title: str | None, code: str) -> str:
    return title.strip() if title and title.strip() else code


def _normalise_segments(
    segments: Iterable[Segment], *, timezone, now_local: datetime
) -> list[RouteSegment]:
    normalised: list[RouteSegment] = []

    for segment in segments:
        if not segment.departure or not segment.arrival:
            continue

        try:
            departure_dt = datetime.fromisoformat(segment.departure).astimezone(
                timezone
            )
            arrival_dt = datetime.fromisoformat(segment.arrival).astimezone(timezone)
        except (ValueError, TypeError) as parse_error:
            logger.debug("Skipping segment due to parse error: %s", parse_error)
            continue

        thread = segment.thread
        thread_number = getattr(thread, "number", None) or ""
        thread_title = getattr(thread, "title", None) or ""
        if thread_number and thread_title and thread_number not in thread_title:
            train_label = f"{thread_number} {thread_title}"
        else:
            train_label = thread_title or thread_number or "Поезд"

        normalised.append(
            RouteSegment(
                departure=departure_dt,
                arrival=arrival_dt,
                train_label=_escape_markdown(train_label),
            )
        )

    normalised.sort(key=lambda item: item.departure)

    if not normalised:
        return []

    grace_threshold = now_local - timedelta(minutes=_PAST_DEPARTURE_GRACE_MINUTES)
    upcoming = [segment for segment in normalised if segment.departure >= grace_threshold]

    return upcoming or normalised


async def send_route_schedule(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    from_code: str,
    to_code: str,
    from_title: str | None,
    to_title: str | None,
) -> None:
    """Send a concise timetable for the configured route in the given direction."""

    if update.message is None:
        logger.debug("send_route_schedule invoked without a message to reply to")
        return

    loading_message = await update.message.reply_text(get_message("loading"))

    config = get_config()
    timezone = config.timezone
    now_local = datetime.now(timezone)

    request = SearchRequest(
        from_=from_code,
        to=to_code,
        date=now_local.strftime("%Y-%m-%d"),
        result_timezone=config.result_timezone,
        limit=200,
    )

    try:
        async with CachedYandexSchedules() as client:
            search_response, was_cached = await client.get_search_results(request)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            "Failed to fetch route schedule %s → %s: %s", from_code, to_code, exc
        )
        await loading_message.edit_text(get_message("error_generic"))
        return

    segments = search_response.segments or []
    normalised_segments = _normalise_segments(
        segments, timezone=timezone, now_local=now_local
    )

    pretty_from = _escape_markdown(_format_station(from_title, from_code))
    pretty_to = _escape_markdown(_format_station(to_title, to_code))

    if not normalised_segments:
        await loading_message.edit_text(
            get_message(
                "route_schedule_no_results",
                from_station=pretty_from,
                to_station=pretty_to,
            )
        )
        return

    display_segments = normalised_segments[:_MAX_RESULTS_TO_SHOW]
    first_departure_date = display_segments[0].departure.strftime("%d.%m")

    lines: list[str] = [
        get_message(
            "route_schedule_title",
            from_station=pretty_from,
            to_station=pretty_to,
        ),
        get_message("route_schedule_updated", time=now_local.strftime("%H:%M")),
        "",
        get_message("route_schedule_list_header", date=first_departure_date),
    ]

    for segment in display_segments:
        lines.append(
            get_message(
                "route_schedule_item",
                departure=segment.departure.strftime("%H:%M"),
                arrival=segment.arrival.strftime("%H:%M"),
                train=segment.train_label,
            )
        )

    remaining = len(normalised_segments) - len(display_segments)
    if remaining > 0:
        lines.append(get_message("route_schedule_more", count=remaining))

    lines.append("")
    lines.append(
        get_message(
            "route_schedule_data_source_cache"
            if was_cached
            else "route_schedule_data_source_api"
        )
    )

    await loading_message.edit_text("\n".join(lines))
