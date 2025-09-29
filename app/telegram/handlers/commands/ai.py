"""AI chat command handler."""

from telegram import Update
from telegram.ext import ContextTypes

from config.log_setup import get_logger
from services.ai.ai_service import AIChatBotService
from services.database.user_service import UserService

logger = get_logger(__name__)

slug = "ai"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ai command for AI chat interactions."""
    if not update.message or not update.effective_user:
        return

    user = update.effective_user
    telegram_id = user.id
    
    # Ensure user exists in database
    await UserService.get_or_create_user(
        telegram_id=telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    # Get prompt from command arguments
    if not context.args:
        await update.message.reply_text(
            "Please provide a prompt for the AI. Usage: /ai <your prompt>"
        )
        return

    prompt = " ".join(context.args)
    logger.info("User %s requested AI prompt: %s", user.username or telegram_id, prompt[:50])

    ai_service = AIChatBotService()
    
    try:
        # Check if user can use AI
        if not await ai_service.can_use_ai(telegram_id):
            await update.message.reply_text(
                "❌ AI chat mode is either disabled or you don't have admin privileges to use it."
            )
            return

        # Send prompt to AI
        response = await ai_service.prompt_ai(telegram_id, prompt)
        
        if response:
            # Split long responses into multiple messages if needed
            max_length = 4096  # Telegram message limit
            if len(response) <= max_length:
                await update.message.reply_text(f"🤖 AI Response:\n\n{response}")
            else:
                # Split into chunks
                chunks = [response[i:i+max_length] for i in range(0, len(response), max_length)]
                for i, chunk in enumerate(chunks):
                    prefix = f"🤖 AI Response (part {i+1}/{len(chunks)}):\n\n" if len(chunks) > 1 else "🤖 AI Response:\n\n"
                    await update.message.reply_text(f"{prefix}{chunk}")
        else:
            await update.message.reply_text(
                "❌ Failed to get AI response. Please try again later."
            )

    except Exception as e:
        logger.error("Error in AI command for user %s: %s", telegram_id, e)
        await update.message.reply_text(
            "❌ An error occurred while processing your AI request."
        )
    
    finally:
        await ai_service.close()