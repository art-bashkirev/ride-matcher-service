from telegram import Update
from telegram.ext import ContextTypes

from app.telegram.utils import is_valid_station_id
from services.ai.flag_service import AIFlagService
from services.ai.nvidia_client import NvidiaAIClient
from config.settings import get_config
from config.log_setup import get_logger

logger = get_logger(__name__)


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command text messages - either echo or AI based on flag."""
    if not update.message or not update.message.text:
        return
    
    message_text = update.message.text.strip()
    
    # Check if it's a station ID - handle as before
    if is_valid_station_id(message_text):
        await update.message.reply_text(f"Use /schedule {message_text} for schedule info.")
        return
    
    # Check AI mode flag
    async with AIFlagService() as flag_service:
        ai_mode_enabled = await flag_service.is_ai_mode_enabled()
    
    if ai_mode_enabled:
        # Use AI to respond
        try:
            config = get_config()
            if not config.nvidia_api_key:
                logger.warning("AI mode enabled but NVIDIA_API_KEY not configured")
                await update.message.reply_text("AI mode is enabled but not properly configured.")
                return
            
            async with NvidiaAIClient(config.nvidia_api_key) as ai_client:
                ai_response = await ai_client.chat_completion(message_text)
                await update.message.reply_text(ai_response)
                logger.info("AI response sent to user %s", update.effective_user.username if update.effective_user else "unknown")
        
        except Exception as e:
            logger.error("Error during AI processing: %s", e)
            await update.message.reply_text("I'm sorry, I'm having trouble processing your message right now.")
    
    else:
        # Echo mode (original behavior)
        await update.message.reply_text(f"Echo: {message_text}")
