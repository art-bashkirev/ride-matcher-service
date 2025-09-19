from __future__ import annotations
from telegram import Update, ForceReply
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from app.telegram.utils import is_valid_station_id
from app.telegram.flows.schedule import schedule

logger = get_logger(__name__)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    user = update.effective_user
    mention = user.mention_html() if user else "there"
    logger.info("User %s started the bot", user.username if user else "unknown")
    await update.message.reply_html(rf"Hi {mention}!", reply_markup=ForceReply(selective=True))

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        logger.info("User %s requested help", update.effective_user.username if update.effective_user else "unknown")
        await update.message.reply_text("Help!")

async def echo_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    message_text = update.message.text.strip()
    # If the message is a valid station id, prompt to use the /schedule command
    if is_valid_station_id(message_text):
        await update.message.reply_text("For schedule information, please use the /schedule <station id> command.")
    else:
        await update.message.reply_text(message_text)
