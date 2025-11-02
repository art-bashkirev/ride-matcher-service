from telegram import Update
from telegram.ext import ContextTypes

from app.telegram.utils import is_valid_station_id, escape_markdown_v2
from app.telegram.messages import get_message
from services.ai.flag_service import AIFlagService
from services.ai.nvidia_client import NvidiaAIClient
from config.settings import get_config, Config
from config.log_setup import get_logger

logger = get_logger(__name__)


async def _handle_ai_mode(
    update: Update, message_text: str, user_info: str, config: Config
):
    """Handle AI mode message processing with comprehensive error handling."""
    try:
        if not config.nvidia_api_key:
            logger.warning(
                "AI mode enabled but NVIDIA_API_KEY not configured for user %s",
                user_info,
            )
            await update.message.reply_text(get_message("ai_mode_not_configured"))
            return

        logger.debug("Starting AI processing for user %s", user_info)

        async with NvidiaAIClient(config.nvidia_api_key) as ai_client:
            ai_response = await ai_client.chat_completion(message_text)

            if not ai_response:
                logger.warning(
                    "AI client returned empty response for user %s", user_info
                )
                await update.message.reply_text(get_message("ai_empty_response"))
                return

            # Send AI response as plain text to avoid MarkdownV2 parsing issues
            # AI responses can contain any characters that may conflict with Markdown
            await update.message.reply_text(ai_response, parse_mode=None)
            logger.info("AI response sent successfully to user %s", user_info)

    except ConnectionError as e:
        logger.error(
            "Connection error during AI processing for user %s: %s", user_info, e
        )
        await update.message.reply_text(get_message("ai_connection_error"))

    except TimeoutError as e:
        logger.error("Timeout error during AI processing for user %s: %s", user_info, e)
        await update.message.reply_text(get_message("ai_timeout_error"))

    except ValueError as e:
        logger.error("Invalid input for AI processing for user %s: %s", user_info, e)
        await update.message.reply_text(get_message("ai_invalid_input"))

    except Exception as e:
        logger.error(
            "Unexpected error during AI processing for user %s: %s", user_info, e
        )
        await update.message.reply_text(get_message("ai_processing_error"))


async def _handle_echo_mode(update: Update, message_text: str, user_info: str):
    """Handle Echo mode message processing with comprehensive error handling."""
    try:
        # Validate message length for echo
        if len(message_text) > 4000:  # Telegram message limit is 4096 characters
            logger.warning(
                "Message too long for echo from user %s (length: %d)",
                user_info,
                len(message_text),
            )
            await update.message.reply_text(get_message("echo_message_too_long"))
            return

        echo_response = f"Echo: {message_text}"
        # Send echo response as plain text to avoid MarkdownV2 parsing issues
        # User messages can contain any characters that may conflict with Markdown
        await update.message.reply_text(echo_response, parse_mode=None)
        logger.info("Echo response sent successfully to user %s", user_info)

    except Exception as e:
        logger.error("Error during Echo mode processing for user %s: %s", user_info, e)
        try:
            await update.message.reply_text(get_message("echo_technical_error"))
        except Exception as send_error:
            logger.error(
                "Failed to send error message to user %s: %s", user_info, send_error
            )


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

    logger.debug(
        "Processing message from user %s: %s",
        user_info,
        message_text[:50] + "..." if len(message_text) > 50 else message_text,
    )

    # Check if it's a keyboard button message and handle it
    keyboard_buttons = {
        get_message("keyboard_schedule_base"): "schedule_base",
        get_message("keyboard_schedule_dest"): "schedule_dest",
        get_message("keyboard_goto"): "goto",
        get_message("keyboard_goback"): "goback",
        get_message("keyboard_cancelride"): "cancelride",
        get_message("keyboard_help"): "help",
        get_message("keyboard_profile"): "profile",
    }

    if message_text in keyboard_buttons:
        button_action = keyboard_buttons[message_text]
        logger.debug("Keyboard button pressed by user %s: %s", user_info, button_action)

        # Get user's stations for schedule buttons
        from services.database.user_service import UserService

        user = update.effective_user
        telegram_id = getattr(user, "id", None) if user else None

        if button_action in [
            "schedule_base",
            "schedule_dest",
            "goto",
            "goback",
            "cancelride",
        ]:
            if not telegram_id:
                await update.message.reply_text(get_message("error_generic"))
                return

            db_user = await UserService.get_user(telegram_id)

            if db_user is None:
                if button_action != "cancelride":
                    await update.message.reply_text(
                        get_message("echo_set_stations_first")
                    )
                else:
                    await update.message.reply_text(get_message("error_generic"))
                return

            base_station_code = db_user.base_station_code or ""
            destination_station_code = db_user.destination_code or ""

            if (not base_station_code or not destination_station_code) and (
                button_action != "cancelride"
            ):
                await update.message.reply_text(get_message("echo_set_stations_first"))
                return

            # Trigger appropriate command
            if button_action in ("schedule_base", "schedule_dest"):
                from app.telegram.handlers.commands.route_schedule import (
                    send_route_schedule,
                )

                if button_action == "schedule_base":
                    await send_route_schedule(
                        update,
                        context,
                        from_code=base_station_code,
                        to_code=destination_station_code,
                        from_title=db_user.base_station_title,
                        to_title=db_user.destination_title,
                    )
                else:
                    await send_route_schedule(
                        update,
                        context,
                        from_code=destination_station_code,
                        to_code=base_station_code,
                        from_title=db_user.destination_title,
                        to_title=db_user.base_station_title,
                    )
                return
            elif button_action == "goto":
                from app.telegram.handlers.commands.goto import goto_command

                await goto_command(update, context)
                return
            elif button_action == "goback":
                from app.telegram.handlers.commands.goback import goback_command

                await goback_command(update, context)
                return
            elif button_action == "cancelride":
                from app.telegram.handlers.commands.cancelride import cancelride_command

                await cancelride_command(update, context)
                return

        if button_action == "help":
            from app.telegram.handlers.commands.help import function as help_function

            await help_function(update, context)
            return
        elif button_action == "profile":
            from app.telegram.handlers.commands.profile import (
                function as profile_function,
            )

            await profile_function(update, context)
            return

    # Check if it's a station ID - handle as before
    if is_valid_station_id(message_text):
        try:
            await update.message.reply_text(
                get_message("echo_station_id_suggestion", station_id=escape_markdown_v2(message_text))
            )
            logger.debug(
                "Station ID suggestion sent to user %s for: %s", user_info, message_text
            )
        except Exception as e:
            logger.error(
                "Failed to send station ID suggestion to user %s: %s", user_info, e
            )
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
