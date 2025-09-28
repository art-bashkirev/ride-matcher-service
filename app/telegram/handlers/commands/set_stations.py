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

from config.log_setup import get_logger
from services.database.user_service import UserService
from services.mongodb.stations_service import get_stations_service

logger = get_logger(__name__)

# Conversation states
CHOOSING_BASE, CHOOSING_DEST, CONFIRM = range(3)

# Callback data prefixes
STATION_SELECT = "station_select:"
STATION_CONFIRM = "station_confirm:"


async def start_set_stations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the set stations conversation."""
    user = update.effective_user
    if not user or not hasattr(user, "id") or update.message is None:
        return ConversationHandler.END
    logger.info(f"User {user.id} started set stations")

    # Store user data
    if not hasattr(context, "user_data") or context.user_data is None:
        context.user_data = {}
    context.user_data["telegram_id"] = user.id
    context.user_data["username"] = getattr(user, "username", None)
    context.user_data["first_name"] = getattr(user, "first_name", None)
    context.user_data["last_name"] = getattr(user, "last_name", None)

    # Check if user already has stations set
    from services.database.user_service import UserService
    db_user = await UserService.get_user(user.id)
    if db_user and db_user.base_station_code and db_user.destination_code:
        await update.message.reply_text(
            "You have already set your stations. Updating is not allowed."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Let's set up your base station and destination.\n\n"
        "First, what's your base station? (the station you usually start from)\n"
        "Please enter the station name or code:"
    )
    return CHOOSING_BASE


async def handle_base_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle base station input."""
    if update.message is None or not hasattr(update.message, "text") or context.user_data is None:
        return CHOOSING_BASE
    query = (update.message.text or "").strip()
    if not query:
        await update.message.reply_text("Please enter a station name or code.")
        return CHOOSING_BASE

    # Search for stations
    service = get_stations_service()
    try:
        stations = await service.search_stations(query, limit=5)
    except Exception as e:
        logger.error(f"Failed to search stations: {e}")
        await update.message.reply_text("Sorry, there was an error searching stations. Please try again.")
        return CHOOSING_BASE

    if not stations:
        await update.message.reply_text(
            f"No stations found for '{query}'. Please try a different name or code."
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
        f"Found {len(stations)} stations. Please select your base station:",
        reply_markup=reply_markup
    )
    return CHOOSING_BASE  # Stay in state until selection


async def handle_station_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle station selection from inline keyboard."""
    query = update.callback_query
    if query is None or not hasattr(query, "data") or context.user_data is None:
        return ConversationHandler.END
    await query.answer()

    data = query.data
    if not (isinstance(data, str) and data.startswith(STATION_SELECT)):
        return ConversationHandler.END

    parts = data[len(STATION_SELECT):].split(":", 1)
    if len(parts) != 2:
        return ConversationHandler.END

    station_type, code = parts

    # Get station details
    service = get_stations_service()
    try:
        station = await service.get_station_by_code(code)
    except Exception as e:
        logger.error(f"Failed to get station {code}: {e}")
        await query.edit_message_text("Error retrieving station details. Please try again.")
        return ConversationHandler.END

    if not station:
        await query.edit_message_text("Station not found. Please try again.")
        return ConversationHandler.END

    # Store selection
    if station_type == "base":
        context.user_data["base_station"] = station
        title = getattr(station, "title", "-") if hasattr(station, "title") else "-"
        code = getattr(station, "code", "-") if hasattr(station, "code") else "-"
        settlement_title = getattr(station, "settlement_title", "-") if hasattr(station, "settlement_title") else "-"
        await query.edit_message_text(
            f"Base station set to: {title} ({code}) - {settlement_title}\n\n"
            "Now, what's your destination station? (where you change from suburban to metro)\n"
            "Please enter the station name or code:"
        )
        return CHOOSING_DEST
    elif station_type == "dest":
        context.user_data["destination_station"] = station
        base = context.user_data.get("base_station") if context.user_data else None
        dest = station
        base_title = getattr(base, "title", "-") if base and hasattr(base, "title") else "-"
        base_code = getattr(base, "code", "-") if base and hasattr(base, "code") else "-"
        base_settlement = getattr(base, "settlement_title", "-") if base and hasattr(base, "settlement_title") else "-"
        dest_title = getattr(dest, "title", "-") if dest and hasattr(dest, "title") else "-"
        dest_code = getattr(dest, "code", "-") if dest and hasattr(dest, "code") else "-"
        dest_settlement = getattr(dest, "settlement_title", "-") if dest and hasattr(dest, "settlement_title") else "-"
        keyboard = [
            [InlineKeyboardButton("Yes, save", callback_data=f"{STATION_CONFIRM}yes")],
            [InlineKeyboardButton("No, start over", callback_data=f"{STATION_CONFIRM}no")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Please confirm your settings:\n\n"
            f"Base station: {base_title} ({base_code}) - {base_settlement}\n"
            f"Destination: {dest_title} ({dest_code}) - {dest_settlement}\n\n"
            "Is this correct?",
            reply_markup=reply_markup
        )
        return CONFIRM


async def handle_destination_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle destination station input."""
    if update.message is None or not hasattr(update.message, "text"):
        return CHOOSING_DEST
    query = (update.message.text or "").strip()
    if not query:
        await update.message.reply_text("Please enter a station name or code.")
        return CHOOSING_DEST

    # Search for stations
    service = get_stations_service()
    try:
        stations = await service.search_stations(query, limit=5)
    except Exception as e:
        logger.error(f"Failed to search stations: {e}")
        await update.message.reply_text("Sorry, there was an error searching stations. Please try again.")
        return CHOOSING_DEST

    if not stations:
        await update.message.reply_text(
            f"No stations found for '{query}'. Please try a different name or code."
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
        f"Found {len(stations)} stations. Please select your destination station:",
        reply_markup=reply_markup
    )
    return CHOOSING_DEST


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle confirmation."""
    query = update.callback_query
    if query is None or not hasattr(query, "data"):
        return ConversationHandler.END
    await query.answer()

    data = query.data
    if not (isinstance(data, str) and data.startswith(STATION_CONFIRM)):
        return ConversationHandler.END

    confirm = data[len(STATION_CONFIRM):]

    if confirm == "no":
        await query.edit_message_text("Cancelled. Use /setstations to start again.")
        return ConversationHandler.END

    # Save to database
    user_data = context.user_data if context.user_data else {}
    base = user_data.get("base_station") if user_data else None
    dest = user_data.get("destination_station") if user_data else None

    if not base or not dest:
        await query.edit_message_text("Missing station data. Please start over.")
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
            await query.edit_message_text("Missing required data. Please start over.")
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
        await query.edit_message_text(
            "✅ Stations saved successfully!\n\n"
            f"Base: {base_title} ({base_code})\n"
            f"Destination: {dest_title} ({dest_code})"
        )
    except Exception as e:
        logger.error(f"Failed to save user stations: {e}")
        await query.edit_message_text("Failed to save stations. Please try again.")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("Operation cancelled.")
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