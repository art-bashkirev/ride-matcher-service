"""Go Back command: Search for trains from destination to base and find matches."""

from telegram import Update
from telegram.ext import ContextTypes

from .ride_search import search_rides


async def goback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for trains from destination station to base and find matches."""
    await search_rides(update, context, reverse=True)


# For registry
slug = "goback"
function = goback_command
