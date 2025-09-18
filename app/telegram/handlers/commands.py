from __future__ import annotations
from telegram import Update, ForceReply
from telegram.ext import ContextTypes

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    user = update.effective_user
    mention = user.mention_html() if user else "there"
    await update.message.reply_html(rf"Hi {mention}!", reply_markup=ForceReply(selective=True))

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Help!")

async def echo_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        await update.message.reply_text(update.message.text)

__all__ = ["cmd_start", "cmd_help", "echo_text"]
