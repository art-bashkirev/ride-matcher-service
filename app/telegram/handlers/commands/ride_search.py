"""Shared ride search functionality for the intent-driven goto/goback commands."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Optional

from telegram import Update
from telegram.ext import ContextTypes

from app.telegram.messages import get_message
from app.telegram.utils import escape_markdown_v2
from config.log_setup import get_logger
from config.settings import get_config
from services.mongodb.thread_matching_service import (
    CandidateThread,
    UserIntent,
    get_thread_matching_service,
)
from services.yandex_schedules.cached_client import CachedYandexSchedules
from services.yandex_schedules.models.search import SearchRequest

logger = get_logger(__name__)


@dataclass(slots=True)
class RideUserProfile:
    """Snapshot of the ride-related data we need about the user."""

    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    base_station_code: str
    base_station_title: str
    destination_code: str
    destination_title: str


@dataclass(slots=True)
class TravelIntentWindow:
    """Goal captured from the user about their desired arrival window."""

    direction: Literal["forward", "reverse"]
    arrival_window_start: datetime
    arrival_window_end: datetime
    tolerance_minutes: int


@dataclass(slots=True)
class RideSearchRequest:
    """Full context required to execute the ride search."""

    profile: RideUserProfile
    intent: TravelIntentWindow


async def search_rides(
    update: Update, context: ContextTypes.DEFAULT_TYPE, request: RideSearchRequest
) -> None:
    """Execute the ride search given a pre-captured intent."""

    if update.message is None:
        logger.warning("search_rides called without a message to respond to")
        return

    telegram_user = update.effective_user
    telegram_id = request.profile.telegram_id

    if telegram_user is None or getattr(telegram_user, "id", None) != telegram_id:
        logger.warning(
            "Mismatch between effective user and provided profile (user=%s, profile=%s)",
            getattr(telegram_user, "id", None),
            telegram_id,
        )

    command = "goback" if request.intent.direction == "reverse" else "goto"
    logger.info(
        "User %s (username: %s) invoked /%s with intent %s-%s",
        telegram_id,
        getattr(telegram_user, "username", "unknown"),
        command,
        request.intent.arrival_window_start.isoformat(),
        request.intent.arrival_window_end.isoformat(),
    )

    config = get_config()
    timezone = config.timezone
    from_code, to_code, from_title, to_title = _resolve_directional_route(
        request.profile, request.intent.direction
    )
    start_local = request.intent.arrival_window_start.astimezone(timezone)
    end_local = request.intent.arrival_window_end.astimezone(timezone)

    searching_msg = await update.message.reply_text(
        get_message(
            "ride_search_searching_goal",
            station=escape_markdown_v2(to_title) if to_title else get_message("ride_intent_unknown_station"),
            start=start_local.strftime("%H:%M"),
            end=end_local.strftime("%H:%M"),
        )
    )

    try:
        target_date = start_local.date()
        search_req = SearchRequest(
            from_=from_code,
            to=to_code,
            date=target_date.strftime("%Y-%m-%d"),
            result_timezone=config.result_timezone,
            limit=300,
        )

        logger.info(
            "Fetching search results for user %s (%s → %s) on %s",
            telegram_id,
            from_code,
            to_code,
            target_date,
        )

        async with CachedYandexSchedules() as cached_client:
            search_response, was_cached = await cached_client.get_search_results(
                search_req
            )

        segments = search_response.segments or []
        logger.debug(
            "Search response for %s: cached=%s, segments=%d",
            telegram_id,
            was_cached,
            len(segments),
        )

        if not segments:
            await searching_msg.edit_text(
                get_message(
                    "ride_search_no_trains_window",
                    start=start_local.strftime("%H:%M"),
                    end=end_local.strftime("%H:%M"),
                )
            )
            return

        candidate_threads: list[CandidateThread] = []
        for segment in segments:
            if not segment.departure or not segment.arrival or not segment.thread:
                continue

            try:
                arrival_dt = datetime.fromisoformat(segment.arrival).astimezone(
                    timezone
                )
                departure_dt = datetime.fromisoformat(segment.departure).astimezone(
                    timezone
                )
            except (ValueError, AttributeError) as parse_error:
                logger.debug("Failed to parse segment timestamps: %s", parse_error)
                continue

            if not (
                request.intent.arrival_window_start
                <= arrival_dt
                <= request.intent.arrival_window_end
            ):
                continue

            thread = CandidateThread(
                thread_uid=segment.thread.uid or "",
                departure_time=departure_dt.isoformat(),
                arrival_time=arrival_dt.isoformat(),
                from_station_code=from_code,
                to_station_code=to_code,
                from_station_title=from_title,
                to_station_title=to_title,
            )
            candidate_threads.append(thread)

        if not candidate_threads:
            logger.info(
                "User %s has no trains matching arrival window %s-%s",
                telegram_id,
                request.intent.arrival_window_start,
                request.intent.arrival_window_end,
            )
            await searching_msg.edit_text(
                get_message(
                    "ride_search_no_trains_window",
                    start=start_local.strftime("%H:%M"),
                    end=end_local.strftime("%H:%M"),
                )
            )
            return

        logger.info(
            "User %s has %d candidate trains for arrival window %s-%s",
            telegram_id,
            len(candidate_threads),
            request.intent.arrival_window_start.isoformat(),
            request.intent.arrival_window_end.isoformat(),
        )

        thread_service = get_thread_matching_service()
        ttl_minutes = _calculate_dynamic_ttl_minutes(request.intent, timezone)
        user_intent_doc = UserIntent(
            direction=request.intent.direction,
            arrival_window_start=request.intent.arrival_window_start,
            arrival_window_end=request.intent.arrival_window_end,
            timezone=config.result_timezone,
            tolerance_minutes=request.intent.tolerance_minutes,
        )

        success = await thread_service.store_search_results(
            telegram_id=telegram_id,
            username=request.profile.username,
            first_name=request.profile.first_name,
            last_name=request.profile.last_name,
            from_station_code=from_code,
            to_station_code=to_code,
            from_station_title=from_title,
            to_station_title=to_title,
            candidate_threads=candidate_threads,
            intent=user_intent_doc,
            ttl_minutes=ttl_minutes,
        )

        if not success:
            logger.error("Failed to store search results for user %s", telegram_id)
            await searching_msg.edit_text(get_message("ride_search_error"))
            return

        thread_uids = [thread.thread_uid for thread in candidate_threads]
        users_to_notify = await thread_service.find_users_to_notify(
            telegram_id, thread_uids
        )

        if users_to_notify:
            logger.info(
                "Notifying %d existing users about new match for user %s",
                len(users_to_notify),
                telegram_id,
            )
            for user_info in users_to_notify:
                try:
                    notification_text = (
                        f"{get_message('ride_new_match')}\n\n"
                        f"{get_message(
                            'ride_new_match_details',
                            thread_title=escape_markdown_v2('совпадающий маршрут'),
                            departure='см. ваш поиск',
                            name=escape_markdown_v2(user_info['new_user_name']),
                            from_=escape_markdown_v2(user_info['new_user_from_title']),
                            to=escape_markdown_v2(user_info['new_user_to_title']),
                        )}"
                    )
                    await context.bot.send_message(
                        chat_id=user_info["telegram_id"], text=notification_text
                    )
                except Exception as send_error:
                    logger.error(
                        "Failed to notify user %s: %s",
                        user_info.get("telegram_id"),
                        send_error,
                    )

        matches = await thread_service.find_matches(telegram_id)
        logger.info(
            "User %s has %d matching threads with other users",
            telegram_id,
            len(matches),
        )

        response_lines = [
            get_message("ride_search_success"),
            get_message(
                "ride_search_found_trains_window",
                count=len(candidate_threads),
                start=start_local.strftime("%H:%M"),
                end=end_local.strftime("%H:%M"),
            ),
            "",
        ]

        response_lines.append("🚂 *Доступные поезда:*")
        for thread in candidate_threads[:10]:
            departure_dt = datetime.fromisoformat(thread.departure_time).astimezone(
                timezone
            )
            arrival_dt = datetime.fromisoformat(thread.arrival_time).astimezone(
                timezone
            )
            response_lines.append(
                f"  • {departure_dt.strftime('%H:%M')} → {arrival_dt.strftime('%H:%M')}"
            )

        if len(candidate_threads) > 10:
            response_lines.append(
                f"  \\.\\.\\.  и ещё {len(candidate_threads) - 10}"
            )

        if matches:
            response_lines.append("")
            response_lines.append(get_message("ride_search_matches_found"))
            for thread_uid, matched_users in matches.items():
                thread_info = next(
                    (candidate for candidate in candidate_threads if candidate.thread_uid == thread_uid),
                    None,
                )
                departure_str = "?"
                if thread_info is not None:
                    departure_str = (
                        datetime.fromisoformat(thread_info.departure_time)
                        .astimezone(timezone)
                        .strftime("%H:%M")
                    )

                response_lines.append("")
                response_lines.append(
                    get_message(
                        "ride_search_match_thread",
                        thread_title=escape_markdown_v2(thread_uid[:8] + "..."),
                        departure=departure_str,
                    )
                )

                for matched_user in matched_users:
                    first_name = matched_user.get("first_name") or ""
                    last_name = matched_user.get("last_name") or ""
                    username = matched_user.get("username") or ""

                    if first_name and last_name:
                        name = f"{first_name} {last_name}"
                    elif first_name:
                        name = first_name
                    elif username:
                        name = username
                    else:
                        name = "Пользователь"

                    response_lines.append(
                        get_message(
                            "ride_search_match_user",
                            name=escape_markdown_v2(name),
                            from_=escape_markdown_v2(matched_user.get("from_station_title", "?")),
                            to=escape_markdown_v2(matched_user.get("to_station_title", "?")),
                        )
                    )
        else:
            response_lines.append("")
            response_lines.append(get_message("ride_search_no_matches"))

        await searching_msg.edit_text("\n".join(response_lines))

        logger.info("User %s /%s command completed successfully", telegram_id, command)

    except Exception as exc:
        logger.error(
            "Error in %s_command for user %s: %s",
            command,
            telegram_id,
            exc,
            exc_info=True,
        )
        await searching_msg.edit_text(get_message("ride_search_error"))


def _resolve_directional_route(
    profile: RideUserProfile, direction: Literal["forward", "reverse"]
) -> tuple[str, str, str, str]:
    if direction == "reverse":
        return (
            profile.destination_code,
            profile.base_station_code,
            profile.destination_title or "",
            profile.base_station_title or "",
        )
    return (
        profile.base_station_code,
        profile.destination_code,
        profile.base_station_title or "",
        profile.destination_title or "",
    )


def _calculate_dynamic_ttl_minutes(
    intent: TravelIntentWindow, timezone
) -> int:
    """Give each search result a TTL long enough to stay relevant."""

    now = datetime.now(timezone)
    window_end = intent.arrival_window_end
    if window_end.tzinfo is None:
        window_end = timezone.localize(window_end)

    minutes_until_goal = max(
        0,
        int((window_end - now).total_seconds() // 60),
    )

    # Keep search results around a bit longer so matches can materialise.
    ttl = minutes_until_goal + 60
    return max(ttl, 60)
