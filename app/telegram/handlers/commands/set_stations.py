"""Set user stations command with conversation handler."""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from typing import Dict, Any
from types import SimpleNamespace

from config.log_setup import get_logger
from services.database.user_service import UserService
from services.mongodb.stations_service import get_stations_service
from app.telegram.messages import get_message

logger = get_logger(__name__)

# Conversation states
CHOOSING_BASE, CHOOSING_DEST, CONFIRM = range(3)

# Callback data prefixes
STATION_SELECT = "station_select:"
STATION_CONFIRM = "station_confirm:"


## Insert helper function for creating station objects


def _station_details(station: Any) -> Dict[str, str]:
    """Extract display-friendly station details with safe fallbacks."""
    if not station:
        return {"title": "-", "code": "-", "settlement": "-"}

    title = getattr(station, "title", "-") or "-"
    code = getattr(station, "code", "-") or "-"
    settlement = getattr(station, "settlement_title", "-") or "-"

    return {"title": title, "code": code, "settlement": settlement}


async def start_set_stations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the set stations conversation."""
    user = update.effective_user
    if not user or not hasattr(user, "id") or update.message is None:
        return ConversationHandler.END
    logger.info("User %s started set stations", user.username if user.username else user.id)

    # Store user data
    if not hasattr(context, "user_data") or context.user_data is None:
        context.user_data = {}
    context.user_data["telegram_id"] = user.id
    context.user_data["username"] = getattr(user, "username", None)
    context.user_data["first_name"] = getattr(user, "first_name", None)
    context.user_data["last_name"] = getattr(user, "last_name", None)

    # Check if user already has stations set
    db_user = await UserService.get_user(user.id)
    if db_user:
        base_exists = bool(getattr(db_user, 'base_station_code', None))
        dest_exists = bool(getattr(db_user, 'destination_code', None))
        if base_exists and dest_exists:
            logger.info("User %s already has stations set, preventing update", user.username if user.username else user.id)
            await update.message.reply_text(get_message("setstations_already_set"))
            return ConversationHandler.END
        elif base_exists and not dest_exists:
            context.user_data['base_station'] = SimpleNamespace(
                code=db_user.base_station_code,
                title=db_user.base_station_title,
                settlement_title=getattr(db_user, 'base_station_settlement', 'Unknown'),
                direction=''
            )
            base_title = getattr(db_user, 'base_station_title', '-') or '-'
            base_code = getattr(db_user, 'base_station_code', '-') or '-'
            logger.info("User %s has base station set but missing destination, prompting for destination", user.username if user.username else user.id)
            await update.message.reply_text(
                get_message(
                    "setstations_destination_pending",
                    base_title=base_title,
                    base_code=base_code,
                )
            )
            return CHOOSING_DEST
        elif dest_exists and not base_exists:
            context.user_data['destination_station'] = SimpleNamespace(
                code=db_user.destination_code,
                title=db_user.destination_title,
                settlement_title=getattr(db_user, 'destination_settlement', 'Unknown'),
                direction=''
            )
            dest_title = getattr(db_user, 'destination_title', '-') or '-'
            dest_code = getattr(db_user, 'destination_code', '-') or '-'
            logger.info("User %s has destination station set but missing base, prompting for base station", user.username if user.username else user.id)
            await update.message.reply_text(
                get_message(
                    "setstations_base_pending",
                    dest_title=dest_title,
                    dest_code=dest_code,
                )
            )
            return CHOOSING_BASE

    logger.info("User %s entering base station selection", user.username if user.username else user.id)

    separator = get_message("separator")
    intro_message = (
        f"{get_message('setstations_title')}\n"
        f"{separator}\n\n"
        f"{get_message('setstations_step1')}\n\n"
        f"{get_message('setstations_intro_description')}\n\n"
        f"{get_message('setstations_how_to_enter')}\n"
        f"{get_message('setstations_entry_options')}\n\n"
        f"{get_message('setstations_enter_base')}"
    )
    await update.message.reply_text(intro_message)
    return CHOOSING_BASE


async def handle_base_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle base station input."""
    if update.message is None or not hasattr(update.message, "text") or context.user_data is None:
        return CHOOSING_BASE
    query = (update.message.text or "").strip()
    if not query:
        await update.message.reply_text(get_message("setstations_empty_input"))
        return CHOOSING_BASE

    user = update.effective_user
    if user is not None:
        if user.username:
            user_id = user.username
        else:
            user_id = user.id
    else:
        user_id = "unknown"
    logger.info("User %s searching for base station with query: '%s'", user_id, query)

    # Search for stations
    service = get_stations_service()
    try:
        stations = await service.search_stations(query, limit=5)
        logger.info("User %s base station search returned %d results", user_id, len(stations) if stations else 0)
    except Exception as e:
        logger.error("User %s failed to search stations: %s", user_id, e)
        await update.message.reply_text(get_message("setstations_search_error"))
        return CHOOSING_BASE

    if not stations:
        logger.info("User %s base station search found no results for query: '%s'", user_id, query)
        await update.message.reply_text(
            get_message("setstations_no_stations_found", query=query)
        )
        return CHOOSING_BASE

    # Show options
    keyboard = []
    for station in stations:
        callback_data = f"{STATION_SELECT}base:{station.code}"
        button_text = f"{station.title} ({station.code}) - {station.settlement_title}"
        if station.direction:
            button_text += f" [{station.direction}]"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        get_message(
            "setstations_stations_found",
            count=len(stations),
            station_type=get_message("setstations_type_base"),
        ),
        reply_markup=reply_markup
    )
    return CHOOSING_BASE  # Stay in state until selection


async def handle_station_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle station selection from inline keyboard."""
    query = update.callback_query
    if query is None or not hasattr(query, "data") or context.user_data is None:
        return ConversationHandler.END
    await query.answer()

    user = update.effective_user
    if user is not None:
        user_id = user.username if user.username else user.id
    else:
        user_id = "unknown"

    data = query.data
    if not (isinstance(data, str) and data.startswith(STATION_SELECT)):
        return ConversationHandler.END

    parts = data[len(STATION_SELECT):].split(":", 1)
    if len(parts) != 2:
        return ConversationHandler.END

    station_type, code = parts
    logger.info("User %s selected %s station with code: %s", user_id, station_type, code)

    service = get_stations_service()
    try:
        station = await service.get_station_by_code(code)
    except Exception as e:
        logger.error("User %s failed to get station %s: %s", user_id, code, e)
        await query.edit_message_text(get_message("setstations_station_fetch_error"))
        return ConversationHandler.END

    if not station:
        logger.warning("User %s selected non-existent station with code: %s", user_id, code)
        await query.edit_message_text(get_message("setstations_station_not_found"))
        return ConversationHandler.END

    station_details = _station_details(station)
    separator = get_message("separator")
    location_label = get_message("setstations_location")

    if station_type == "base":
        context.user_data["base_station"] = station
        logger.info(
            "User %s set base station: %s (%s) - %s",
            user_id,
            station_details["title"],
            station_details["code"],
            station_details["settlement"],
        )
        existing_dest = context.user_data.get("destination_station") if context.user_data else None
        if existing_dest:
            dest_details = _station_details(existing_dest)
            keyboard = [
                [InlineKeyboardButton(get_message("setstations_button_yes"), callback_data=f"{STATION_CONFIRM}yes")],
                [InlineKeyboardButton(get_message("setstations_button_no"), callback_data=f"{STATION_CONFIRM}no")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            logger.info(
                "User %s entering confirmation with base: %s (%s), dest: %s (%s)",
                user_id,
                station_details["title"],
                station_details["code"],
                dest_details["title"],
                dest_details["code"],
            )
            confirmation_text = (
                f"{get_message('setstations_confirm_title')}\n"
                f"{separator}\n\n"
                f"{get_message('setstations_base_station_section')}\n"
                f"{get_message('setstations_station_summary', title=station_details['title'], code=station_details['code'], settlement=station_details['settlement'], location_label=location_label)}\n\n"
                f"{get_message('setstations_destination_section')}\n"
                f"{get_message('setstations_station_summary', title=dest_details['title'], code=dest_details['code'], settlement=dest_details['settlement'], location_label=location_label)}\n\n"
                f"{get_message('setstations_confirm_question')}"
            )
            await query.edit_message_text(confirmation_text, reply_markup=reply_markup)
            return CONFIRM

        base_summary = get_message(
            "setstations_station_summary",
            title=station_details["title"],
            code=station_details["code"],
            settlement=station_details["settlement"],
            location_label=location_label,
        )
        message_text = (
            f"{get_message('setstations_base_set_success')}\n"
            f"{separator}\n\n"
            f"{get_message('setstations_base_station_section')}\n"
            f"{base_summary}\n\n"
            f"{get_message('setstations_next_step')}\n"
            f"{get_message('setstations_enter_destination')}"
        )
        await query.edit_message_text(message_text)
        return CHOOSING_DEST

    if station_type == "dest":
        context.user_data["destination_station"] = station
        dest_details = station_details
        base = context.user_data.get("base_station") if context.user_data else None
        base_details = _station_details(base)
        logger.info(
            "User %s set destination station: %s (%s) - %s",
            user_id,
            dest_details["title"],
            dest_details["code"],
            dest_details["settlement"],
        )
        logger.info(
            "User %s entering confirmation with base: %s (%s), dest: %s (%s)",
            user_id,
            base_details["title"],
            base_details["code"],
            dest_details["title"],
            dest_details["code"],
        )
        keyboard = [
            [InlineKeyboardButton(get_message("setstations_button_yes"), callback_data=f"{STATION_CONFIRM}yes")],
            [InlineKeyboardButton(get_message("setstations_button_no"), callback_data=f"{STATION_CONFIRM}no")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        confirmation_text = (
            f"{get_message('setstations_confirm_title')}\n"
            f"{separator}\n\n"
            f"{get_message('setstations_base_station_section')}\n"
            f"{get_message('setstations_station_summary', title=base_details['title'], code=base_details['code'], settlement=base_details['settlement'], location_label=location_label)}\n\n"
            f"{get_message('setstations_destination_section')}\n"
            f"{get_message('setstations_station_summary', title=dest_details['title'], code=dest_details['code'], settlement=dest_details['settlement'], location_label=location_label)}\n\n"
            f"{get_message('setstations_confirm_question')}"
        )
        await query.edit_message_text(confirmation_text, reply_markup=reply_markup)
        return CONFIRM

    return ConversationHandler.END


async def handle_destination_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle destination station input."""
    if update.message is None or not hasattr(update.message, "text"):
        return CHOOSING_DEST
    query = (update.message.text or "").strip()
    if not query:
        await update.message.reply_text(get_message("setstations_empty_input"))
        return CHOOSING_DEST

    user = update.effective_user
    if user is not None:
        if user.username:
            user_id = user.username
        else:
            user_id = user.id
    else:
        user_id = "unknown"
    logger.info("User %s searching for destination station with query: '%s'", user_id, query)

    # Search for stations
    service = get_stations_service()
    try:
        stations = await service.search_stations(query, limit=5)
        logger.info("User %s destination station search returned %d results", user_id, len(stations) if stations else 0)
    except Exception as e:
        logger.error("User %s failed to search stations: %s", user_id, e)
        await update.message.reply_text(get_message("setstations_search_error"))
        return CHOOSING_DEST

    if not stations:
        logger.info("User %s destination station search found no results for query: '%s'", user_id, query)
        await update.message.reply_text(
            get_message("setstations_no_stations_found", query=query)
        )
        return CHOOSING_DEST

    # Show options
    keyboard = []
    for station in stations:
        callback_data = f"{STATION_SELECT}dest:{station.code}"
        button_text = f"{station.title} ({station.code}) - {station.settlement_title}"
        if station.direction:
            button_text += f" [{station.direction}]"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        get_message(
            "setstations_stations_found",
            count=len(stations),
            station_type=get_message("setstations_type_destination"),
        ),
        reply_markup=reply_markup
    )
    return CHOOSING_DEST


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle confirmation."""
    query = update.callback_query
    if query is None or not hasattr(query, "data"):
        return ConversationHandler.END
    await query.answer()

    user = update.effective_user
    if user is not None:
        if user.username:
            user_id = user.username
        else:
            user_id = user.id
    else:
        user_id = "unknown"

    data = query.data
    if not (isinstance(data, str) and data.startswith(STATION_CONFIRM)):
        return ConversationHandler.END

    confirm = data[len(STATION_CONFIRM):]

    if confirm == "no":
        logger.info("User %s cancelled station setup", user_id)
        await query.edit_message_text(get_message("setstations_cancelled_restart"))
        return ConversationHandler.END

    logger.info("User %s confirmed station setup, saving to database", user_id)

    # Save to database
    user_data = context.user_data if context.user_data else {}
    base = user_data.get("base_station") if user_data else None
    dest = user_data.get("destination_station") if user_data else None

    if not base or not dest:
        logger.error("User %s missing station data during confirmation", user_id)
        await query.edit_message_text(get_message("setstations_missing_data"))
        return ConversationHandler.END

    try:
        # Ensure user exists
        telegram_id = user_data.get("telegram_id")
        username = user_data.get("username", "")
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")
        base_code = getattr(base, "code", "") if base and hasattr(base, "code") else ""
        base_title = getattr(base, "title", "") if base and hasattr(base, "title") else ""
        dest_code = getattr(dest, "code", "") if dest and hasattr(dest, "code") else ""
        dest_title = getattr(dest, "title", "") if dest and hasattr(dest, "title") else ""
        # Only proceed if all required fields are present
        if not (isinstance(telegram_id, int) and base_code and base_title and dest_code and dest_title):
            logger.error("User %s missing required data for saving stations", user_id)
            await query.edit_message_text(get_message("setstations_missing_data"))
            return ConversationHandler.END
        await UserService.get_or_create_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        await UserService.update_user_stations(
            telegram_id=telegram_id,
            base_station_code=base_code,
            base_station_title=base_title,
            destination_code=dest_code,
            destination_title=dest_title,
        )
        logger.info("User %s successfully saved stations: base=%s (%s), dest=%s (%s)", 
                   user_id, base_title, base_code, dest_title, dest_code)
        base_details = _station_details(base)
        dest_details = _station_details(dest)
        separator = get_message("separator")
        location_label = get_message("setstations_location")
        success_text = (
            f"{get_message('setstations_success_title')}\n"
            f"{separator}\n\n"
            f"{get_message('setstations_base_station_section')}\n"
            f"{get_message('setstations_station_summary', title=base_details['title'], code=base_details['code'], settlement=base_details['settlement'], location_label=location_label)}\n\n"
            f"{get_message('setstations_destination_section')}\n"
            f"{get_message('setstations_station_summary', title=dest_details['title'], code=dest_details['code'], settlement=dest_details['settlement'], location_label=location_label)}\n\n"
            f"{get_message('setstations_success_message')}"
        )
        await query.edit_message_text(success_text)
    except Exception as e:
        logger.error("User %s failed to save user stations: %s", user_id, e)
        await query.edit_message_text(get_message("setstations_save_error"))

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    user = update.effective_user
    user_id = user.username if user and user.username else (user.id if user else "unknown")
    logger.info("User %s cancelled set stations conversation", user_id)
    if update.message is not None:
        await update.message.reply_text(get_message("setstations_cancelled"))
    elif update.callback_query is not None:
        await update.callback_query.edit_message_text(get_message("setstations_cancelled"))
    else:
        # Fallback if neither message nor callback_query is available
        pass
    return ConversationHandler.END


# Conversation handler
set_stations_handler = ConversationHandler(
    entry_points=[CommandHandler("setstations", start_set_stations)],
    states={
        CHOOSING_BASE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_base_station),
            CallbackQueryHandler(handle_station_selection, pattern=f"^{STATION_SELECT}"),
        ],
        CHOOSING_DEST: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_destination_station),
            CallbackQueryHandler(handle_station_selection, pattern=f"^{STATION_SELECT}"),
        ],
        CONFIRM: [
            CallbackQueryHandler(handle_confirmation, pattern=f"^{STATION_CONFIRM}"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# For registry
slug = "setstations"
function = set_stations_handler