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
    "separator": "═══════════════════════",
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
    "setstations_intro_description": "Давайте настроим вашу базовую станцию (место начала поездки).",
    "setstations_entry_options": '• Название станции (например, "Москва-Пассажирская")\n• Код станции (например, "s1234567")',
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
    "setstations_stations_found": "Найдено {count} станций. Пожалуйста, выберите вашу {station_type} станцию:",
    "setstations_no_stations_found": "Станции для '{query}' не найдены. Попробуйте другое название или код.",
    "setstations_already_set": "Вы уже настроили станции. Обновление пока недоступно. Введите /cancel, чтобы отменить.",
    "setstations_destination_pending": "Мы сохранили вашу базовую станцию: {base_title} ({base_code}).\nПожалуйста, укажите станцию назначения. Введите /cancel, чтобы отменить.",
    "setstations_base_pending": "Мы сохранили вашу станцию назначения: {dest_title} ({dest_code}).\nПожалуйста, укажите базовую станцию. Введите /cancel, чтобы отменить.",
    "setstations_empty_input": "Пожалуйста, введите название или код станции.",
    "setstations_search_error": "Не удалось выполнить поиск станций. Пожалуйста, попробуйте ещё раз.",
    "setstations_type_base": "базовую",
    "setstations_type_destination": "станцию назначения",
    "setstations_station_summary": "     📍 {title}\n     🔗 Код: {code}\n     🌍 {location_label} {settlement}",
    "setstations_button_yes": "Да, сохранить",
    "setstations_button_no": "Нет, начать заново",
    "setstations_station_fetch_error": "Не удалось получить данные станции. Пожалуйста, попробуйте ещё раз.",
    "setstations_station_not_found": "Станция не найдена. Пожалуйста, попробуйте ещё раз.",
    "setstations_cancelled_restart": "Настройка отменена. Используйте /setstations, чтобы начать заново.",
    "setstations_missing_data": "Отсутствуют необходимые данные. Пожалуйста, начните заново.",
    "setstations_save_error": "Не удалось сохранить станции. Пожалуйста, попробуйте ещё раз.",
    "setstations_cancelled": "Операция отменена. Введите /cancel для выхода.",
    # Commands
    "help_title": f"{EMOJIS['help']} **Доступные команды**",
    "help_commands": f"""
{EMOJIS['start']} /start - Инициализировать бота
{EMOJIS['help']} /help - Показать это сообщение помощи
{EMOJIS['train']} /schedule - Посмотреть расписание поездов
{EMOJIS['stats']} /stats - Посмотреть статистику кэша
{EMOJIS['user']} /profile - Посмотреть ваш профиль
{EMOJIS['settings']} /setstations - Установить ваши станции
🚂 /goto - Найти поезда и попутчиков (база → пункт назначения)
🔙 /goback - Найти поезда и попутчиков (пункт назначения → база)
❌ /cancelride - Отменить поиск попутчиков""",
    "help_need_help": f"{EMOJIS['tip']} **Нужна помощь?** Просто введите команду для начала!",
    "start_welcome": f"{EMOJIS['celebration']} **Добро пожаловать в Ride Matcher!**",
    "start_get_started": f"{EMOJIS['start']} **Начать работу:**",
    "start_ready": "Готовы исследовать? Введите /help для начала!",
    "start_greeting_with_stations": "Привет, {mention}! Я здесь, чтобы помочь вам с расписанием поездов.",
    "start_greeting_no_stations": "Привет, {mention}! Я здесь, чтобы помочь вам с расписанием поездов и информацией о станциях.",
    "start_your_base_station": EMOJIS["home"]
    + " **Ваша базовая станция:** {base_station}",
    "start_your_destination": EMOJIS["target"] + " **Ваше назначение:** {destination}",
    "start_use_menu": "Используйте меню ниже для проверки расписания!",
    "start_set_stations_instruction": "• Используйте /setstations для настройки ваших станций (обязательно)",
    "start_help_instruction": "• Используйте /help для просмотра всех доступных команд",
    "start_please_set_stations": "⚠️ Пожалуйста, сначала установите ваши станции с помощью /setstations!",
    "test_title": "**Тестовая команда**",
    "test_quote": '*"Мы нужны им такими, какие мы есть. Так что будьте собой. Только лучше."*',
    "test_working": f"{EMOJIS['success']} Бот работает отлично!",
    "stats_title": f"{EMOJIS['stats']} **Статистика кэша**",
    "stats_intro": "Привет, {mention}! Вот текущая статистика кэша:",
    "stats_message": "**Статистика:** {stats}",
    "stats_tip": f"{EMOJIS['tip']} *Кэш помогает улучшить время отклика, сохраняя часто используемые данные.*",
    # Schedule Command
    "schedule_cmd_help_title": f"{EMOJIS['train']} **Помощь по команде расписания**",
    "schedule_cmd_missing_id": f"{EMOJIS['question']} **Отсутствует ID станции**",
    "schedule_cmd_usage": "**Использование:**\n`/schedule s9600213`",
    "schedule_cmd_format": "**Формат:**\n• ID станции: 's' + 7 цифр\n• Пример: s9600213",
    "schedule_cmd_tip": f"{EMOJIS['tip']} **Совет:** Используйте /setstations для настройки ваших станций!",
    "schedule_error_invalid_format": f"{EMOJIS['error']} **Неверный формат ID станции**",
    "schedule_error_you_entered": "**Вы ввели:** `{station_id}`",
    "schedule_error_expected_format": "**Ожидаемый формат:**\n• 's' с последующими 7 цифрами\n• Пример: s9600213",
    "schedule_error_try_again": f"{EMOJIS['tip']} **Попробуйте еще раз с правильным форматом!**",
    "schedule_data_source_cache": "💾 Данные из кэша",
    "schedule_data_source_api": "🌐 Свежие данные из API",
    "schedule_station_info": "\n🏛️ Станция: {title}{station_type}",
    "schedule_invalid_station_id": f"{EMOJIS['error']} Неверный формат ID станции",
    "schedule_loading_schedule": "{emoji} Загрузка расписания...".format(
        emoji=EMOJIS["loading"]
    ),
    "schedule_loading_page": "{emoji} Загрузка страницы...".format(
        emoji=EMOJIS["loading"]
    ),
    "schedule_error_loading_schedule": f"{EMOJIS['error']} Не удалось загрузить расписание. Пожалуйста, попробуйте ещё раз.",
    "schedule_error_loading_page": f"{EMOJIS['error']} Не удалось загрузить страницу расписания. Пожалуйста, попробуйте ещё раз.",
    "schedule_invalid_page_number": f"{EMOJIS['error']} Неверный номер страницы",
    "schedule_no_upcoming_departures": f"{EMOJIS['schedule']} Ближайшие отправления для станции "
    "{station_id} на {date} не найдены.",
    "schedule_no_departures_generic": f"{EMOJIS['schedule']} Отправления для станции "
    "{station_id} на {date} не найдены.",
    # Errors
    "error_try_different_date": "• Попробуйте другую дату",
    "error_check_station_id": "• Проверьте ID станции",
    "error_contact_support": "• Обратитесь в поддержку при необходимости",
    # Keyboard buttons
    "keyboard_schedule_base": f"{EMOJIS['home']} Моё расписание",
    "keyboard_schedule_dest": f"{EMOJIS['target']} Расписание до пункта назначения",
    "keyboard_goto": "🚂 Найти попутчиков (туда)",
    "keyboard_goback": "🔙 Найти попутчиков (обратно)",
    "keyboard_cancelride": "❌ Отменить поиск",
    "keyboard_help": f"{EMOJIS['help']} Помощь",
    "keyboard_profile": f"{EMOJIS['user']} Профиль",
    # Echo/Message handlers
    "echo_station_id_suggestion": "Используйте /schedule {station_id} для получения информации о расписании.",
    "echo_set_stations_first": "⚠️ Пожалуйста, сначала установите ваши станции с помощью /setstations!",
    # AI Mode messages
    "ai_mode_not_configured": "Режим AI включён, но не настроен должным образом.",
    "ai_empty_response": "Я получил пустой ответ от AI. Пожалуйста, попробуйте еще раз.",
    "ai_connection_error": "У меня проблемы с подключением к сервису AI. Пожалуйста, попробуйте позже.",
    "ai_timeout_error": "Сервис AI слишком долго отвечает. Пожалуйста, попробуйте еще раз.",
    "ai_invalid_input": "Я не смог обработать ваше сообщение. Пожалуйста, попробуйте перефразировать.",
    "ai_processing_error": "Извините, у меня сейчас проблемы с обработкой вашего сообщения.",
    "ai_mode_start_required": "Сначала запустите бота командой /start.",
    "ai_mode_admin_only": "Эта команда доступна только администраторам.",
    "ai_mode_permission_error": "❌ Не удалось проверить ваши права. Пожалуйста, попробуйте позже.",
    "ai_mode_status_enabled": "включён",
    "ai_mode_status_disabled": "выключен",
    "ai_mode_status": "Режим AI сейчас *{status}*.",
    "ai_mode_usage_hint": "Используйте `/ai_mode on` для включения или `/ai_mode off` для отключения режима AI.",
    "ai_mode_invalid_command": "Неверная команда. Используйте:\n• `/ai_mode on` для включения\n• `/ai_mode off` для отключения\n• `/ai_mode` для проверки текущего статуса",
    "ai_mode_updated": "✅ Режим AI был *{status}*.",
    "ai_mode_update_failed": "❌ Не удалось обновить режим AI. Пожалуйста, попробуйте позже.",
    "ai_mode_error_checking": "❌ Не удалось проверить статус режима AI. Пожалуйста, попробуйте позже.",
    "ai_mode_error_updating": "❌ Произошла ошибка при обновлении режима AI. Пожалуйста, попробуйте позже.",
    # Echo Mode messages
    "echo_message_too_long": "Ваше сообщение слишком длинное для эха. Пожалуйста, отправьте более короткое сообщение.",
    "echo_technical_error": "Извините, я не смог повторить ваше сообщение из-за технической проблемы.",
    # Ride Matching messages
    "ride_search_title": f"{EMOJIS['train']} **Поиск попутчиков**",
    "ride_search_searching": f"{EMOJIS['loading']} Ищу поезда и попутчиков...",
    "ride_search_searching_goal": f"{EMOJIS['loading']} Ищу поезда и попутчиков для прибытия в {{station}} между {{start}} и {{end}}...",
    "ride_search_no_stations": "⚠️ Сначала установите станции с помощью /setstations!",
    "ride_search_error": f"{EMOJIS['error']} Не удалось выполнить поиск. Попробуйте позже.",
    "ride_search_no_trains": f"{EMOJIS['error']} Поездов не найдено в ближайший час.",
    "ride_search_no_trains_window": f"{EMOJIS['error']} Поездов не найдено для прибытия между {{start}} и {{end}}.",
    "ride_search_success": f"{EMOJIS['success']} **Поиск завершен!**",
    "ride_search_found_trains": "Найдено {count} поездов в ближайший час.",
    "ride_search_found_trains_window": "Найдено {count} поездов для прибытия между {start} и {end}.",
    "ride_search_matches_found": f"{EMOJIS['celebration']} **Найдены попутчики!**",
    "ride_search_no_matches": "Пока попутчиков не найдено. Мы уведомим вас, когда кто-то найдется!",
    "ride_search_match_thread": "🚂 **Поезд:** {thread_title} (отправление: {departure})",
    "ride_search_match_user": "👤 {name} ({from_} → {to})",
    "ride_search_cancelled": "Поиск попутчиков отменен.",
    "ride_cancel_success": f"{EMOJIS['success']} Ваш поиск попутчиков отменен.",
    "ride_cancel_nothing": "У вас нет активных поисков попутчиков.",
    "ride_new_match": f"{EMOJIS['celebration']} **Новый попутчик найден!**",
    "ride_new_match_details": "🚂 Поезд: {thread_title}\n⏰ Отправление: {departure}\n👤 Попутчик: {name}\n📍 Маршрут: {from_} → {to}",
    "ride_intent_prompt": f"{EMOJIS['question']} **Когда вы хотите прибыть в {EMOJIS['target']} {{station}}?**\nВведите время, например `08:45` или `08:30-09:00`.",
    "ride_intent_unknown_station": "вашу станцию",
    "ride_intent_invalid_time": "Не удалось распознать время. Используйте формат `HH:MM` или диапазон `HH:MM-HH:MM`.",
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
