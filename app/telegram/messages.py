"""Russian message templates for the Telegram bot."""

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

# Russian message templates
MESSAGES = {
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
    
    # Echo/Message handlers
    "echo_station_id_suggestion": "Используйте /schedule {{station_id}} для получения информации о расписании.",
    
    # AI Mode messages
    "ai_mode_not_configured": "Режим AI включён, но не настроен должным образом.",
    "ai_empty_response": "Я получил пустой ответ от AI. Пожалуйста, попробуйте еще раз.",
    "ai_connection_error": "У меня проблемы с подключением к сервису AI. Пожалуйста, попробуйте позже.",
    "ai_timeout_error": "Сервис AI слишком долго отвечает. Пожалуйста, попробуйте еще раз.",
    "ai_invalid_input": "Я не смог обработать ваше сообщение. Пожалуйста, попробуйте перефразировать.",
    "ai_processing_error": "Извините, у меня сейчас проблемы с обработкой вашего сообщения.",
    
    # Echo Mode messages
    "echo_message_too_long": "Ваше сообщение слишком длинное для эха. Пожалуйста, отправьте более короткое сообщение.",
    "echo_technical_error": "Извините, я не смог повторить ваше сообщение из-за технической проблемы.",
}


def get_message(key: str, **kwargs) -> str:
    """Get a message template and format it with provided variables.
    
    Args:
        key: Message key to retrieve
        **kwargs: Variables to format into the message
        
    Returns:
        Formatted message
    """
    try:
        template = MESSAGES[key]
    except KeyError:
        return f"[Missing message: {key}]"
    
    # Format template with provided variables
    try:
        return template.format(**kwargs)
    except (KeyError, ValueError):
        # Return template without formatting if error occurs
        return template
