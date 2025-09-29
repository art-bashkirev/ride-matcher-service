"""Internationalization types and enums."""

from enum import Enum
from typing import Literal


class Language(str, Enum):
    """Supported languages for the bot."""
    EN = "en"
    RU = "ru"


# Type alias for message keys
MessageKey = Literal[
    # Common
    "loading",
    "error_generic",
    "cancel",
    "yes",
    "no",
    "back",
    "next",
    "previous",
    
    # Schedule
    "schedule_title",
    "schedule_station",
    "schedule_page",
    "schedule_no_departures",
    "schedule_no_departures_suggestions",
    "schedule_arrives",
    "schedule_departs",
    "schedule_departure",
    "schedule_arrival",
    "schedule_platform",
    "schedule_stops",
    "schedule_time_na",
    
    # Profile
    "profile_title",
    "profile_username",
    "profile_first_name",
    "profile_last_name",
    "profile_base_station",
    "profile_destination",
    "profile_code",
    "profile_not_found",
    "profile_not_set",
    
    # Set Stations
    "setstations_title",
    "setstations_step1",
    "setstations_how_to_enter",
    "setstations_enter_base",
    "setstations_base_set_success",
    "setstations_next_step",
    "setstations_enter_destination",
    "setstations_confirm_title",
    "setstations_base_station_section",
    "setstations_destination_section",
    "setstations_location",
    "setstations_confirm_question",
    "setstations_success_title",
    "setstations_success_message",
    "setstations_stations_found",
    "setstations_no_stations_found",
    
    # Commands
    "help_title",
    "help_commands",
    "help_need_help",
    "start_welcome",
    "start_get_started",
    "start_ready",
    "test_title",
    "test_quote",
    "test_working",
    "stats_title",
    "stats_message",
    "stats_tip",
    
    # Schedule Command
    "schedule_cmd_help_title",
    "schedule_cmd_missing_id",
    "schedule_cmd_usage",
    "schedule_cmd_format",
    "schedule_cmd_tip",
    "schedule_error_invalid_format",
    "schedule_error_you_entered",
    "schedule_error_expected_format",
    "schedule_error_try_again",
    
    # Errors
    "error_try_different_date",
    "error_check_station_id",
    "error_contact_support",
]