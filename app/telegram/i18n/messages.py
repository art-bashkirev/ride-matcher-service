"""Message templates with simple, clear emoji choices."""

from .types import Language

# Simple, clear emoji choices that work well in Telegram
EMOJIS = {
    # Transportation
    "train": "🚂",
    "station": "🚉",
    "time": "🕒",
    "schedule": "📅",
    "route": "📍",
    
    # Status and actions
    "loading": "⏳",
    "success": "✅",
    "error": "❌",
    "question": "❓",
    
    # Profile and user
    "user": "👤",
    "home": "🏠",
    "target": "🎯",
    
    # Interface
    "help": "❓",
    "start": "🚀",
    "stats": "📊",
    "settings": "⚙️",
    "tip": "💡",
    "celebration": "🎉",
}

# Message templates for English
MESSAGES_EN = {
    # Common
    "loading": f"{EMOJIS['loading']} **Fetching data...**\n\nPlease wait...",
    "error_generic": f"{EMOJIS['error']} **Error**\n\nSomething went wrong. Please try again.",
    
    # Schedule
    "schedule_title": f"{EMOJIS['schedule']} **Schedule for {{date}}**",
    "schedule_station": f"{EMOJIS['station']} **Station:** {{station_id}}{{station_name}}",
    "schedule_page": f"📄 **Page {{current_page}}/{{total_pages}}**",
    "schedule_no_departures": f"{EMOJIS['schedule']} **No Departures Found**",
    "schedule_no_departures_suggestions": f"{EMOJIS['tip']} **Suggestions:**\n• Try a different date\n• Check the station ID\n• Contact support if needed",
    "schedule_arrives": "Arr",
    "schedule_departs": "Dep",
    "schedule_departure": "Departure",
    "schedule_arrival": "Arrival",
    "schedule_platform": "Platform",
    "schedule_stops": "Stops",
    "schedule_time_na": f"{EMOJIS['time']} Time: N/A",
    
    # Profile
    "profile_title": f"{EMOJIS['user']} **Profile Information**",
    "profile_username": "**Username:**",
    "profile_first_name": "**First Name:**",
    "profile_last_name": "**Last Name:**",
    "profile_base_station": f"{EMOJIS['home']} **Base Station:**",
    "profile_destination": f"{EMOJIS['target']} **Destination:**",
    "profile_code": "Code:",
    "profile_not_found": "No profile found. Please set your stations first with /setstations.",
    "profile_not_set": "Not set",
    
    # Set Stations
    "setstations_title": f"{EMOJIS['train']} **Station Setup Wizard**",
    "setstations_step1": f"{EMOJIS['home']} **Step 1: Base Station**",
    "setstations_how_to_enter": f"{EMOJIS['tip']} **How to enter:**",
    "setstations_enter_base": "Please type your base station name or code:",
    "setstations_base_set_success": f"{EMOJIS['success']} **Base Station Set Successfully!**",
    "setstations_next_step": f"{EMOJIS['target']} **Next Step:** Please enter your destination station",
    "setstations_enter_destination": f"{EMOJIS['tip']} **Tip:** Enter the station name or code below",
    "setstations_confirm_title": f"{EMOJIS['success']} **Confirm Your Station Settings**",
    "setstations_base_station_section": f"{EMOJIS['home']} **Base Station:**",
    "setstations_destination_section": f"{EMOJIS['target']} **Destination Station:**",
    "setstations_location": "Location:",
    "setstations_confirm_question": f"{EMOJIS['question']} **Is this information correct?**",
    "setstations_success_title": f"{EMOJIS['celebration']} **Stations Saved Successfully!**",
    "setstations_success_message": "Your stations have been saved and are ready to use!",
    "setstations_stations_found": "Found {{count}} stations. Please select your {{type}} station:",
    "setstations_no_stations_found": "No stations found for '{{query}}'. Please try a different name or code.",
    
    # Commands  
    "help_title": f"{EMOJIS['help']} **Available Commands**",
    "help_commands": f"""
{EMOJIS['start']} /start - Initialize the bot
{EMOJIS['help']} /help - Show this help message
{EMOJIS['train']} /schedule - View train schedules
{EMOJIS['stats']} /stats - View cache statistics
{EMOJIS['user']} /profile - View your profile
{EMOJIS['settings']} /setstations - Set your stations""",
    "help_need_help": f"{EMOJIS['tip']} **Need help?** Just type a command to get started!",
    
    "start_welcome": f"{EMOJIS['celebration']} **Welcome to Ride Matcher!**",
    "start_get_started": f"{EMOJIS['start']} **Get Started:**",
    "start_ready": "Ready to explore? Type /help to begin!",
    
    "test_title": "**Test Command**",
    "test_quote": "*\"They need us for who we are. So be yourself. Only better.\"*",
    "test_working": f"{EMOJIS['success']} Bot is working perfectly!",
    
    "stats_title": f"{EMOJIS['stats']} **Cache Statistics**",
    "stats_message": "Here are the current cache statistics:\n\n**Stats:** {{stats}}",
    "stats_tip": f"{EMOJIS['tip']} *Cache helps improve response times by storing frequently accessed data.*",
    
    # Schedule Command
    "schedule_cmd_help_title": f"{EMOJIS['train']} **Schedule Command Help**",
    "schedule_cmd_missing_id": f"{EMOJIS['question']} **Missing Station ID**",
    "schedule_cmd_usage": "**Usage:**\n`/schedule s9600213`",
    "schedule_cmd_format": "**Format:**\n• Station ID: 's' + 7 digits\n• Example: s9600213",
    "schedule_cmd_tip": f"{EMOJIS['tip']} **Tip:** Use /setstations to configure your stations first!",
    
    "schedule_error_invalid_format": f"{EMOJIS['error']} **Invalid Station ID Format**",
    "schedule_error_you_entered": "**You entered:** `{{station_id}}`",
    "schedule_error_expected_format": "**Expected format:**\n• 's' followed by exactly 7 digits\n• Example: s9600213",
    "schedule_error_try_again": f"{EMOJIS['tip']} **Try again with correct format!**",
    
    # Errors
    "error_try_different_date": "• Try a different date",
    "error_check_station_id": "• Check the station ID",
    "error_contact_support": "• Contact support if needed",
    
    # Keyboard buttons
    "keyboard_schedule_base": f"{EMOJIS['home']} My Schedule",
    "keyboard_schedule_dest": f"{EMOJIS['target']} Destination Schedule",
    "keyboard_help": f"{EMOJIS['help']} Help",
    "keyboard_profile": f"{EMOJIS['user']} Profile",
}

# Message templates for Russian
MESSAGES_RU = {
    # Common
    "loading": f"{EMOJIS['loading']} **Загрузка данных...**\n\nПожалуйста, подождите...",
    "error_generic": f"{EMOJIS['error']} **Ошибка**\n\nЧто-то пошло не так. Пожалуйста, попробуйте еще раз.",
    
    # Schedule
    "schedule_title": f"{EMOJIS['schedule']} **Расписание на {{date}}**",
    "schedule_station": f"{EMOJIS['station']} **Станция:** {{station_id}}{{station_name}}",
    "schedule_page": f"📄 **Страница {{current_page}}/{{total_pages}}**",
    "schedule_no_departures": f"{EMOJIS['schedule']} **Отправления не найдены**",
    "schedule_no_departures_suggestions": f"{EMOJIS['tip']} **Предложения:**\n• Попробуйте другую дату\n• Проверьте ID станции\n• Обратитесь в поддержку при необходимости",
    "schedule_arrives": "Приб",
    "schedule_departs": "Отпр",
    "schedule_departure": "Отправление",
    "schedule_arrival": "Прибытие",
    "schedule_platform": "Платформа",
    "schedule_stops": "Остановки",
    "schedule_time_na": f"{EMOJIS['time']} Время: Н/Д",
    
    # Profile
    "profile_title": f"{EMOJIS['user']} **Информация профиля**",
    "profile_username": "**Имя пользователя:**",
    "profile_first_name": "**Имя:**",
    "profile_last_name": "**Фамилия:**",
    "profile_base_station": f"{EMOJIS['home']} **Базовая станция:**",
    "profile_destination": f"{EMOJIS['target']} **Назначение:**",
    "profile_code": "Код:",
    "profile_not_found": "Профиль не найден. Пожалуйста, сначала установите ваши станции с помощью /setstations.",
    "profile_not_set": "Не установлено",
    
    # Set Stations
    "setstations_title": f"{EMOJIS['train']} **Мастер настройки станций**",
    "setstations_step1": f"{EMOJIS['home']} **Шаг 1: Базовая станция**",
    "setstations_how_to_enter": f"{EMOJIS['tip']} **Как вводить:**",
    "setstations_enter_base": "Пожалуйста, введите название или код вашей базовой станции:",
    "setstations_base_set_success": f"{EMOJIS['success']} **Базовая станция успешно установлена!**",
    "setstations_next_step": f"{EMOJIS['target']} **Следующий шаг:** Пожалуйста, введите станцию назначения",
    "setstations_enter_destination": f"{EMOJIS['tip']} **Совет:** Введите название или код станции ниже",
    "setstations_confirm_title": f"{EMOJIS['success']} **Подтвердите настройки станций**",
    "setstations_base_station_section": f"{EMOJIS['home']} **Базовая станция:**",
    "setstations_destination_section": f"{EMOJIS['target']} **Станция назначения:**",
    "setstations_location": "Местоположение:",
    "setstations_confirm_question": f"{EMOJIS['question']} **Эта информация верна?**",
    "setstations_success_title": f"{EMOJIS['celebration']} **Станции успешно сохранены!**",
    "setstations_success_message": "Ваши станции сохранены и готовы к использованию!",
    "setstations_stations_found": "Найдено {{count}} станций. Пожалуйста, выберите вашу {{type}} станцию:",
    "setstations_no_stations_found": "Станции для '{{query}}' не найдены. Попробуйте другое название или код.",
    
    # Commands  
    "help_title": f"{EMOJIS['help']} **Доступные команды**",
    "help_commands": f"""
{EMOJIS['start']} /start - Инициализировать бота
{EMOJIS['help']} /help - Показать это сообщение помощи
{EMOJIS['train']} /schedule - Посмотреть расписание поездов
{EMOJIS['stats']} /stats - Посмотреть статистику кэша
{EMOJIS['user']} /profile - Посмотреть ваш профиль
{EMOJIS['settings']} /setstations - Установить ваши станции""",
    "help_need_help": f"{EMOJIS['tip']} **Нужна помощь?** Просто введите команду для начала!",
    
    "start_welcome": f"{EMOJIS['celebration']} **Добро пожаловать в Ride Matcher!**",
    "start_get_started": f"{EMOJIS['start']} **Начать работу:**",
    "start_ready": "Готовы исследовать? Введите /help для начала!",
    
    "test_title": "**Тестовая команда**",
    "test_quote": "*\"Мы нужны им такими, какие мы есть. Так что будьте собой. Только лучше.\"*",
    "test_working": f"{EMOJIS['success']} Бот работает отлично!",
    
    "stats_title": f"{EMOJIS['stats']} **Статистика кэша**",
    "stats_message": "Вот текущая статистика кэша:\n\n**Статистика:** {{stats}}",
    "stats_tip": f"{EMOJIS['tip']} *Кэш помогает улучшить время отклика, сохраняя часто используемые данные.*",
    
    # Schedule Command
    "schedule_cmd_help_title": f"{EMOJIS['train']} **Помощь по команде расписания**",
    "schedule_cmd_missing_id": f"{EMOJIS['question']} **Отсутствует ID станции**",
    "schedule_cmd_usage": "**Использование:**\n`/schedule s9600213`",
    "schedule_cmd_format": "**Формат:**\n• ID станции: 's' + 7 цифр\n• Пример: s9600213",
    "schedule_cmd_tip": f"{EMOJIS['tip']} **Совет:** Используйте /setstations для настройки ваших станций!",
    
    "schedule_error_invalid_format": f"{EMOJIS['error']} **Неверный формат ID станции**",
    "schedule_error_you_entered": "**Вы ввели:** `{{station_id}}`",
    "schedule_error_expected_format": "**Ожидаемый формат:**\n• 's' с последующими 7 цифрами\n• Пример: s9600213",
    "schedule_error_try_again": f"{EMOJIS['tip']} **Попробуйте еще раз с правильным форматом!**",
    
    # Errors
    "error_try_different_date": "• Попробуйте другую дату",
    "error_check_station_id": "• Проверьте ID станции",
    "error_contact_support": "• Обратитесь в поддержку при необходимости",
    
    # Keyboard buttons
    "keyboard_schedule_base": f"{EMOJIS['home']} Моё расписание",
    "keyboard_schedule_dest": f"{EMOJIS['target']} Расписание до пункта назначения",
    "keyboard_help": f"{EMOJIS['help']} Помощь",
    "keyboard_profile": f"{EMOJIS['user']} Профиль",
}

# All message templates
MESSAGES = {
    Language.EN: MESSAGES_EN,
    Language.RU: MESSAGES_RU,
}
