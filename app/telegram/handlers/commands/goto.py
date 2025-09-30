"""Go To command: Search for trains from base to destination and find matches."""

from telegram import Update
from telegram.ext import ContextTypes

from .ride_search import search_rides


async def goto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for trains from base station to destination and find matches."""
    await search_rides(update, context, reverse=False)


# For registry
slug = "goto"
function = goto_command
