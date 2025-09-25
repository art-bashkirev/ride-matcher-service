"""Search for stations by name."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from services.database.stations_service import get_stations_service

logger = get_logger(__name__)

slug = "search_station"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search_station command."""
    if not update.message:
        return

    username = update.effective_user.username if update.effective_user else "unknown"

    if not context.args:
        await update.message.reply_text(
            "Please provide a station name to search for.\n\n"
            "Example: `/search_station Moscow` or `/search_station Domodedovo`\n\n"
            "💡 You can search by:\n"
            "• Station name\n"
            "• City/settlement name\n"
            "• Region name"
        )
        logger.info("User %s requested station search without arguments", username)
        return

    query = " ".join(context.args)
    if len(query.strip()) < 2:
        await update.message.reply_text(
            "❌ Search query too short. Please provide at least 2 characters."
        )
        return

    # Show loading message
    loading_message = await update.message.reply_text(f"🔍 Searching for stations: `{query}`...")

    logger.info("User %s searching for stations: %s", username, query)

    try:
        stations_service = get_stations_service()
        
        # Check if stations are available
        total_stations = await stations_service.get_stations_count()
        if total_stations == 0:
            await loading_message.edit_text(
                "❌ No stations data available.\n\n"
                "An administrator needs to run `/fetch_stations` first to load station data."
            )
            return

        # Search for stations
        results = await stations_service.search_stations(query, limit=10)

        if not results:
            await loading_message.edit_text(
                f"❌ No stations found for: `{query}`\n\n"
                "Try:\n"
                "• Different spelling\n"
                "• Shorter search terms\n"
                "• City name instead of station name"
            )
            return

        # Format results
        response_text = f"🔍 **Search results for:** `{query}`\n\n"
        keyboard_buttons = []

        for i, result in enumerate(results[:10], 1):
            station = result.station
            
            # Build location context
            location_parts = []
            if station.settlement_title != station.title:
                location_parts.append(station.settlement_title)
            if station.region_title not in [station.title, station.settlement_title]:
                location_parts.append(station.region_title)
            
            location_text = f" ({', '.join(location_parts)})" if location_parts else ""
            
            # Add transport type emoji
            transport_emoji = {
                "train": "🚆",
                "suburban": "🚊", 
                "bus": "🚌",
                "plane": "✈️",
                "water": "⛴️"
            }.get(station.transport_type, "🚉")
            
            response_text += f"{i}. {transport_emoji} **{station.title}**{location_text}\n"
            
            # Add direction if available
            if station.direction:
                response_text += f"   📍 Direction: {station.direction}\n"
            
            response_text += f"   🆔 Code: `{station.codes.yandex_code}`\n"
            
            if result.relevance_score > 0:
                response_text += f"   📊 Relevance: {result.relevance_score:.2f}\n"
            
            response_text += "\n"
            
            # Add button for getting schedule
            button_text = f"📅 {station.title[:20]}..."
            callback_data = f"schedule_{station.codes.yandex_code}"
            keyboard_buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

        response_text += f"💡 Click a button below to get the schedule, or use `/schedule {results[0].station.codes.yandex_code}` directly."
        
        # Create keyboard
        keyboard = InlineKeyboardMarkup(keyboard_buttons[:5])  # Limit to 5 buttons to avoid message too long

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