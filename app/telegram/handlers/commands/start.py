from telegram import Update, ForceReply, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from app.telegram.messages import get_message
from config.log_setup import get_logger
from services.database.user_service import UserService

logger = get_logger(__name__)

slug = "start"


async def function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    if update.message is None:
        return
    
    user = update.effective_user
    telegram_id = getattr(user, "id", None) if user else None
    mention = user.mention_html() if user else "there"
    
    # Create or update user
    if telegram_id:
        try:
            await UserService.get_or_create_user(telegram_id, user.username, user.first_name, user.last_name)
        except Exception as e:
            logger.warning(f"Could not create/update user: {e}")
    
    logger.info("User %s started the bot", user.username if user else "unknown")
    
    # Check if user has stations configured
    db_user = await UserService.get_user(telegram_id) if telegram_id else None
    has_stations = db_user and db_user.base_station_code and db_user.destination_code
    
    # Build welcome message
    welcome = get_message("start_welcome")
    get_started = get_message("start_get_started")
    ready = get_message("start_ready")
    
    if has_stations:
        # User has stations - show menu keyboard
        keyboard_base = get_message("keyboard_schedule_base")
        keyboard_dest = get_message("keyboard_schedule_dest")
        keyboard_help = get_message("keyboard_help")
        keyboard_profile = get_message("keyboard_profile")
        
        keyboard = [
            [KeyboardButton(keyboard_base), KeyboardButton(keyboard_dest)],
            [KeyboardButton(keyboard_help), KeyboardButton(keyboard_profile)],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        greeting = get_message("start_greeting_with_stations", mention=mention)
        base_station = get_message("start_your_base_station", base_station=db_user.base_station_title)
        destination = get_message("start_your_destination", destination=db_user.destination_title)
        use_menu = get_message("start_use_menu")
        
        await update.message.reply_html(
            f"{welcome}\n\n"
            f"{greeting}\n\n"
            f"{base_station}\n"
            f"{destination}\n\n"
            f"{use_menu}",
            reply_markup=reply_markup
        )
    else:
        # User doesn't have stations - prompt to set them
        greeting = get_message("start_greeting_no_stations", mention=mention)
        set_stations_instruction = get_message("start_set_stations_instruction")
        help_instruction = get_message("start_help_instruction")
        please_set_stations = get_message("start_please_set_stations")
        
        await update.message.reply_html(
            f"{welcome}\n\n"
            f"{greeting}\n\n"
            f"{get_started}\n"
            f"{set_stations_instruction}\n"
            f"{help_instruction}\n\n"
            f"{please_set_stations}",
            reply_markup=ForceReply(selective=True)
        )
