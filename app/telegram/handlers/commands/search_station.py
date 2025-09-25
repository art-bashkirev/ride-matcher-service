"""Search for stations by name."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from services.database.stations_service import get_stations_service

logger = get_logger(__name__)

slug = "search_station"

# Constants
MIN_QUERY_LENGTH = 2
MAX_SEARCH_RESULTS = 10
MAX_KEYBOARD_BUTTONS = 5

HELP_MESSAGE = (
    "Please provide a station name to search for.\n\n"
    "Example: `/search_station Moscow` or `/search_station Domodedovo`\n\n"
    "💡 You can search by:\n"
    "• Station name\n"
    "• City/settlement name\n"
    "• Region name"
)

NO_RESULTS_HELP = (
    "Try:\n"
    "• Different spelling\n"
    "• Shorter search terms\n"
    "• City name instead of station name"
)

TRANSPORT_EMOJIS = {
    "train": "🚆",
    "suburban": "🚊", 
    "bus": "🚌",
    "plane": "✈️",
    "water": "⛴️"
}


def _build_location_context(station) -> str:
    """Build location context string for a station."""
    location_parts = []
    if station.settlement_title != station.title:
        location_parts.append(station.settlement_title)
    if station.region_title not in [station.title, station.settlement_title]:
        location_parts.append(station.region_title)
    return f" ({', '.join(location_parts)})" if location_parts else ""


def _get_transport_emoji(transport_type: str) -> str:
    """Get emoji for transport type."""
    return TRANSPORT_EMOJIS.get(transport_type, "🚉")


def _format_station_result(station, relevance_score: float, index: int) -> str:
    """Format a single station result."""
    location_text = _build_location_context(station)
    transport_emoji = _get_transport_emoji(station.transport_type)
    
    result_text = f"{index}. {transport_emoji} **{station.title}**{location_text}\n"
    
    if station.direction:
        result_text += f"   📍 Direction: {station.direction}\n"
    
    result_text += f"   🆔 Code: `{station.codes.yandex_code}`\n"
    
    if relevance_score > 0:
        result_text += f"   📊 Relevance: {relevance_score:.2f}\n"
    
    return result_text + "\n"


def _create_keyboard_buttons(results) -> list:
    """Create keyboard buttons for search results."""
    keyboard_buttons = []
    for result in results[:MAX_KEYBOARD_BUTTONS]:
        station = result.station
        button_text = f"📅 {station.title[:20]}..."
        callback_data = f"schedule_{station.codes.yandex_code}"
        keyboard_buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    return keyboard_buttons


async def _validate_input(update, context, loading_message) -> tuple[str, str]:
    """Validate user input and return query and username."""
    username = update.effective_user.username if update.effective_user else "unknown"
    
    if not context.args:
        await loading_message.edit_text(HELP_MESSAGE)
        logger.info("User %s requested station search without arguments", username)
        return None, username
    
    query = " ".join(context.args)
    if len(query.strip()) < MIN_QUERY_LENGTH:
        await loading_message.edit_text(
            "❌ Search query too short. Please provide at least 2 characters."
        )
        return None, username
    
    return query, username


async def _check_stations_available(stations_service, loading_message) -> bool:
    """Check if stations data is available, auto-fetch if needed."""
    if await stations_service.ensure_stations_loaded():
        return True
    
    await loading_message.edit_text(
        "❌ No stations data available and auto-fetch failed.\n\n"
        "An administrator can run `/fetch_stations` to manually load station data."
    )
    return False


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search_station command."""
    if not update.message:
        return

    # Show loading message immediately
    loading_message = await update.message.reply_text("🔍 Preparing search...")
    
    # Validate input
    query, username = await _validate_input(update, context, loading_message)
    if not query:
        return
    
    # Update loading message with query
    await loading_message.edit_text(f"🔍 Searching for stations: `{query}`...")
    logger.info("User %s searching for stations: %s", username, query)

    try:
        stations_service = get_stations_service()
        
        # Check if stations are available
        if not await _check_stations_available(stations_service, loading_message):
            return

        # Search for stations
        results = await stations_service.search_stations(query, limit=MAX_SEARCH_RESULTS)

        if not results:
            await loading_message.edit_text(
                f"❌ No stations found for: `{query}`\n\n{NO_RESULTS_HELP}"
            )
            return

        # Format results
        response_text = f"🔍 **Search results for:** `{query}`\n\n"
        
        for i, result in enumerate(results, 1):
            response_text += _format_station_result(result.station, result.relevance_score, i)

        response_text += f"💡 Click a button below to get the schedule, or use `/schedule {results[0].station.codes.yandex_code}` directly."
        
        # Create keyboard and send response
        keyboard_buttons = _create_keyboard_buttons(results)
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        await loading_message.edit_text(response_text, reply_markup=keyboard, parse_mode='Markdown')
        logger.info("Successfully provided %d station search results for user %s", len(results), username)

    except Exception as e:
        logger.error("Error searching stations for query '%s': %s", query, str(e))
        error_message = (
            f"❌ Error searching for stations: `{query}`\n"
            f"Please try again later.\n\n"
            f"Error: {str(e)}"
        )
        
        try:
            await loading_message.edit_text(error_message)
        except Exception:
            await update.message.reply_text(error_message)