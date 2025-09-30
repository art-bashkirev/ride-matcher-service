"""Go To command: Search for trains from base to destination and find matches."""

from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config.log_setup import get_logger
from config.settings import get_config
from services.database.user_service import UserService
from services.yandex_schedules.cached_client import CachedYandexSchedules
from services.yandex_schedules.models.search import SearchRequest
from services.mongodb.thread_matching_service import (
    get_thread_matching_service,
    CandidateThread
)
from app.telegram.messages import get_message

logger = get_logger(__name__)


async def goto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for trains from base station to destination and find matches."""
    user = update.effective_user
    telegram_id = getattr(user, "id", None)
    
    if telegram_id is None or update.message is None:
        logger.warning("goto_command called with no user or message")
        return
    
    # Log command invocation
    logger.info("User %s (username: %s) invoked /goto command", 
                telegram_id, getattr(user, "username", "unknown"))
    
    # Get user from database by telegram_id
    db_user = await UserService.get_user(telegram_id)
    if not db_user or not db_user.base_station_code or not db_user.destination_code:
        logger.warning("User %s attempted /goto without stations configured", telegram_id)
        await update.message.reply_text(get_message("ride_search_no_stations"))
        return
    
    # Show searching message
    searching_msg = await update.message.reply_text(get_message("ride_search_searching"))
    
    try:
        config = get_config()
        
        # Calculate time window: now + 2.5 hours
        now = datetime.now(config.timezone)
        end_time = now + timedelta(hours=2.5)
        
        # Create search request
        search_req = SearchRequest(
            from_=db_user.base_station_code,
            to=db_user.destination_code,
            date=now.strftime('%Y-%m-%d'),
            result_timezone=config.result_timezone,
            limit=300  # Get all trains
        )
        
        logger.info("Fetching search results for user %s: %s -> %s", 
                   telegram_id, db_user.base_station_code, db_user.destination_code)
        
        # Get search results (cached or fresh)
        cached_client = CachedYandexSchedules()
        search_response, was_cached = await cached_client.get_search_results(search_req)
        
        logger.debug("Search results for user %s: cached=%s, segments=%d", 
                    telegram_id, was_cached, len(search_response.segments or []))
        
        if not search_response.segments:
            logger.warning("No train segments found for user %s", telegram_id)
            await searching_msg.edit_text(get_message("ride_search_no_trains"))
            return
        
        # Filter candidate trains within time window
        candidate_threads = []
        for segment in search_response.segments:
            if not segment.departure or not segment.arrival or not segment.thread:
                continue
            
            # Parse departure time
            try:
                departure_dt = datetime.fromisoformat(segment.departure)
                departure_dt = departure_dt.astimezone(config.timezone)
                
                # Check if within time window
                if now <= departure_dt <= end_time:
                    arrival_dt = datetime.fromisoformat(segment.arrival)
                    arrival_dt = arrival_dt.astimezone(config.timezone)
                    
                    thread = CandidateThread(
                        thread_uid=segment.thread.uid or "",
                        departure_time=departure_dt.isoformat(),
                        arrival_time=arrival_dt.isoformat(),
                        from_station_code=db_user.base_station_code,
                        to_station_code=db_user.destination_code,
                        from_station_title=db_user.base_station_title or "",
                        to_station_title=db_user.destination_title or ""
                    )
                    candidate_threads.append(thread)
                    
            except (ValueError, AttributeError) as e:
                logger.debug("Failed to parse segment time: %s", e)
                continue
        
        logger.info("User %s has %d candidate trains in time window", 
                   telegram_id, len(candidate_threads))
        
        if not candidate_threads:
            await searching_msg.edit_text(get_message("ride_search_no_trains"))
            return
        
        # Store search results in MongoDB
        thread_service = get_thread_matching_service()
        success = await thread_service.store_search_results(
            telegram_id=telegram_id,
            username=db_user.username,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            from_station_code=db_user.base_station_code,
            to_station_code=db_user.destination_code,
            from_station_title=db_user.base_station_title or "",
            to_station_title=db_user.destination_title or "",
            candidate_threads=candidate_threads
        )
        
        if not success:
            logger.error("Failed to store search results for user %s", telegram_id)
            await searching_msg.edit_text(get_message("ride_search_error"))
            return
        
        # Find matches
        matches = await thread_service.find_matches(telegram_id)
        
        logger.info("User %s has %d matching threads with other users", 
                   telegram_id, len(matches))
        
        # Build response message
        response_lines = [
            get_message("ride_search_success"),
            get_message("ride_search_found_trains", count=len(candidate_threads))
        ]
        
        if matches:
            response_lines.append("")
            response_lines.append(get_message("ride_search_matches_found"))
            
            for thread_uid, matched_users in matches.items():
                # Find the thread details from our candidate threads
                thread_info = next((t for t in candidate_threads if t.thread_uid == thread_uid), None)
                
                if thread_info:
                    departure_dt = datetime.fromisoformat(thread_info.departure_time)
                    departure_str = departure_dt.strftime("%H:%M")
                    
                    response_lines.append("")
                    response_lines.append(
                        get_message("ride_search_match_thread", 
                                  thread_title=thread_uid[:8] + "...",
                                  departure=departure_str)
                    )
                    
                    for matched_user in matched_users:
                        name = matched_user.get("first_name") or matched_user.get("username") or "Пользователь"
                        from_title = matched_user.get("from_station_title", "?")
                        to_title = matched_user.get("to_station_title", "?")
                        
                        response_lines.append(
                            get_message("ride_search_match_user",
                                      name=name,
                                      from_=from_title,
                                      to=to_title)
                        )
        else:
            response_lines.append("")
            response_lines.append(get_message("ride_search_no_matches"))
        
        await searching_msg.edit_text("\n".join(response_lines))
        
        logger.info("User %s /goto command completed successfully", telegram_id)
        
    except Exception as e:
        logger.error("Error in goto_command for user %s: %s", telegram_id, e, exc_info=True)
        await searching_msg.edit_text(get_message("ride_search_error"))


# For registry
slug = "goto"
function = goto_command
