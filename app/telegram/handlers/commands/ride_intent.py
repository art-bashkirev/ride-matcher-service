"""Conversation helpers for capturing ride intents before executing searches."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, time
from typing import Optional

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.telegram.messages import get_message
from app.telegram.utils import escape_markdown_v2
from config.log_setup import get_logger
from config.settings import get_config
from services.database.user_service import UserService

from .ride_search import (
    RideSearchRequest,
    RideUserProfile,
    TravelIntentWindow,
    search_rides,
)

logger = get_logger(__name__)

ASKING_ARRIVAL = 1
_DEFAULT_TOLERANCE_MINUTES = 15
_TIME_TOKEN = re.compile(r"^(?P<h>\d{1,2})(?::(?P<m>\d{1,2}))?$")
_RANGE_SEPARATORS = re.compile(r"\s*(?:-|–|—|до|to)\s*")


@dataclass(slots=True)
class _RideConversationContext:
    profile: RideUserProfile
    direction: str


def build_ride_conversation(reverse: bool) -> ConversationHandler:
    direction = "reverse" if reverse else "forward"

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message is None:
            return ConversationHandler.END

        user = update.effective_user
        telegram_id = getattr(user, "id", None)
        if telegram_id is None:
            return ConversationHandler.END

        db_user = await UserService.get_user(telegram_id)
        if (
            not db_user
            or not db_user.base_station_code
            or not db_user.destination_code
        ):
            await update.message.reply_text(get_message("ride_search_no_stations"))
            return ConversationHandler.END

        profile = RideUserProfile(
            telegram_id=telegram_id,
            username=db_user.username,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            base_station_code=db_user.base_station_code,
            base_station_title=db_user.base_station_title or "",
            destination_code=db_user.destination_code,
            destination_title=db_user.destination_title or "",
        )

        context.user_data["ride_context"] = _RideConversationContext(
            profile=profile,
            direction=direction,
        )

        arrival_station = (
            profile.base_station_title
            if direction == "reverse"
            else profile.destination_title
        )

        await update.message.reply_text(
            get_message(
                "ride_intent_prompt",
                station=escape_markdown_v2(arrival_station) if arrival_station else get_message("ride_intent_unknown_station"),
            )
        )
        return ASKING_ARRIVAL

    async def handle_arrival(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message is None:
            return ConversationHandler.END

        data: Optional[_RideConversationContext] = context.user_data.get("ride_context")
        if data is None:
            logger.warning("Ride conversation missing cached context")
            await update.message.reply_text(get_message("ride_search_error"))
            return ConversationHandler.END

        raw_input = (update.message.text or "").strip()
        if not raw_input:
            await update.message.reply_text(get_message("ride_intent_invalid_time"))
            return ASKING_ARRIVAL

        config = get_config()
        parsed_intent = _parse_arrival_window(
            raw_input,
            config.timezone,
            direction=data.direction,
        )

        if parsed_intent is None:
            await update.message.reply_text(get_message("ride_intent_invalid_time"))
            return ASKING_ARRIVAL

        request = RideSearchRequest(profile=data.profile, intent=parsed_intent)

        # Clean up stored conversation state before kicking off an async flow
        context.user_data.pop("ride_context", None)

        await search_rides(update, context, request)
        return ConversationHandler.END

    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message is not None:
            await update.message.reply_text(
                get_message("ride_search_cancelled"),
                reply_markup=ReplyKeyboardRemove(),
            )
        context.user_data.pop("ride_context", None)
        return ConversationHandler.END

    return ConversationHandler(
        entry_points=[CommandHandler("goback" if reverse else "goto", start)],
        states={
            ASKING_ARRIVAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_arrival)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


def _parse_arrival_window(
    raw_text: str,
    timezone,
    *,
    direction: str,
    tolerance_minutes: int = _DEFAULT_TOLERANCE_MINUTES,
) -> Optional[TravelIntentWindow]:
    now = datetime.now(timezone)
    cleaned = raw_text.strip().lower()
    parts = _RANGE_SEPARATORS.split(cleaned)

    try:
        if len(parts) >= 2:
            start_time = _parse_time(parts[0])
            end_time = _parse_time(parts[1])
            if start_time is None or end_time is None:
                return None

            start_dt = timezone.localize(
                datetime.combine(now.date(), start_time)
            )
            end_dt = timezone.localize(datetime.combine(now.date(), end_time))

            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
        else:
            center_time = _parse_time(parts[0])
            if center_time is None:
                return None

            center_dt = timezone.localize(
                datetime.combine(now.date(), center_time)
            )
            start_dt = center_dt - timedelta(minutes=tolerance_minutes)
            day_start = timezone.localize(
                datetime.combine(center_dt.date(), time(0, 0))
            )
            if start_dt < day_start:
                start_dt = day_start
            end_dt = center_dt + timedelta(minutes=tolerance_minutes)

        while end_dt <= now + timedelta(minutes=5):
            start_dt += timedelta(days=1)
            end_dt += timedelta(days=1)

        return TravelIntentWindow(
            direction="reverse" if direction == "reverse" else "forward",
            arrival_window_start=start_dt,
            arrival_window_end=end_dt,
            tolerance_minutes=tolerance_minutes if len(parts) == 1 else 0,
        )
    except ValueError:
        return None


def _parse_time(part: str) -> Optional[time]:
    candidate = part.strip()
    if not candidate:
        return None

    candidate = candidate.replace(" ", "")
    candidate = candidate.replace(",", ":").replace(".", ":")

    if candidate.isdigit():
        value = int(candidate)
        if value >= 2400:
            return None
        if value >= 100:
            hours = value // 100
            minutes = value % 100
        else:
            hours = value
            minutes = 0
    else:
        match = _TIME_TOKEN.match(candidate)
        if not match:
            return None
        hours = int(match.group("h"))
        minutes = int(match.group("m") or 0)

    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        return None

    return time(hour=hours, minute=minutes)
