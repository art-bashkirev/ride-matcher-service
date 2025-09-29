from telegram import Update
from telegram.ext import ContextTypes

from app.telegram.utils import is_valid_station_id
from services.ai.flag_service import AIFlagService
from services.ai.nvidia_client import NvidiaAIClient
from config.settings import get_config, Config
from config.log_setup import get_logger

logger = get_logger(__name__)


async def _handle_ai_mode(update: Update, message_text: str, user_info: str, config: Config):
    """Handle AI mode message processing with comprehensive error handling."""
    try:
        if not config.nvidia_api_key:
            logger.warning("AI mode enabled but NVIDIA_API_KEY not configured for user %s", user_info)
            await update.message.reply_text("AI mode is enabled but not properly configured.")
            return
        
        logger.debug("Starting AI processing for user %s", user_info)
        
        async with NvidiaAIClient(config.nvidia_api_key) as ai_client:
            ai_response = await ai_client.chat_completion(message_text)
            
            if not ai_response:
                logger.warning("AI client returned empty response for user %s", user_info)
                await update.message.reply_text("I received an empty response from the AI. Please try again.")
                return
            
            await update.message.reply_text(ai_response)
            logger.info("AI response sent successfully to user %s", user_info)
    
    except ConnectionError as e:
        logger.error("Connection error during AI processing for user %s: %s", user_info, e)
        await update.message.reply_text("I'm having trouble connecting to the AI service. Please try again later.")
    
    except TimeoutError as e:
        logger.error("Timeout error during AI processing for user %s: %s", user_info, e)
        await update.message.reply_text("The AI service is taking too long to respond. Please try again.")
    
    except ValueError as e:
        logger.error("Invalid input for AI processing for user %s: %s", user_info, e)
        await update.message.reply_text("I couldn't process your message. Please try rephrasing it.")
    
    except Exception as e:
        logger.error("Unexpected error during AI processing for user %s: %s", user_info, e)
        await update.message.reply_text("I'm sorry, I'm having trouble processing your message right now.")


async def _handle_echo_mode(update: Update, message_text: str, user_info: str):
    """Handle Echo mode message processing with comprehensive error handling."""
    try:
        # Validate message length for echo
        if len(message_text) > 4000:  # Telegram message limit is 4096 characters
            logger.warning("Message too long for echo from user %s (length: %d)", user_info, len(message_text))
            await update.message.reply_text("Your message is too long to echo. Please send a shorter message.")
            return
        
        echo_response = f"Echo: {message_text}"
        await update.message.reply_text(echo_response)
        logger.info("Echo response sent successfully to user %s", user_info)
    
    except Exception as e:
        logger.error("Error during Echo mode processing for user %s: %s", user_info, e)
        try:
            await update.message.reply_text("I'm sorry, I couldn't echo your message due to a technical issue.")
        except Exception as send_error:
            logger.error("Failed to send error message to user %s: %s", user_info, send_error)


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command text messages - either echo or AI based on flag."""
    if not update.message or not update.message.text:
        logger.debug("Ignoring message without text content")
        return
    
    message_text = update.message.text.strip()
    user_info = update.effective_user.username if update.effective_user else "unknown"
    
    # Input validation and logging
    if not message_text:
        logger.warning("Received empty message from user %s", user_info)
        return
    
    logger.debug("Processing message from user %s: %s", user_info, message_text[:50] + "..." if len(message_text) > 50 else message_text)
    
    # Check if it's a station ID - handle as before
    if is_valid_station_id(message_text):
        try:
            await update.message.reply_text(f"Use /schedule {message_text} for schedule info.")
            logger.debug("Station ID suggestion sent to user %s for: %s", user_info, message_text)
        except Exception as e:
            logger.error("Failed to send station ID suggestion to user %s: %s", user_info, e)
        return
    
    # Check AI mode flag
    try:
        async with AIFlagService() as flag_service:
            ai_mode_enabled = await flag_service.is_ai_mode_enabled()
    except Exception as e:
        logger.error("Failed to check AI mode flag: %s. Defaulting to Echo mode", e)
        ai_mode_enabled = False
    
    config = get_config()
    
    # Environment-based handler logging
    if config.is_development:
        handler_type = "AI" if ai_mode_enabled else "Echo"
        logger.info("Handler invoked: %s mode for user %s", handler_type, user_info)
    
    if ai_mode_enabled:
        # AI mode processing
        await _handle_ai_mode(update, message_text, user_info, config)
    else:
        # Echo mode processing
        await _handle_echo_mode(update, message_text, user_info)
