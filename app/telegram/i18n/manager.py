"""Internationalization manager for the Telegram bot."""

from typing import Dict, Any, Optional
from .types import Language, MessageKey
from .messages import MESSAGES


class I18nManager:
    """Manages internationalization for the bot."""
    
    def __init__(self, default_language: Language = Language.EN):
        """Initialize the i18n manager.
        
        Args:
            default_language: Default language to use if user language is not available
        """
        self.default_language = default_language
        self._user_languages: Dict[int, Language] = {}
    
    def set_user_language(self, user_id: int, language: Language) -> None:
        """Set language preference for a user.
        
        Args:
            user_id: Telegram user ID
            language: Language to set
        """
        self._user_languages[user_id] = language
    
    def get_user_language(self, user_id: int) -> Language:
        """Get language preference for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            User's language preference or default language
        """
        return self._user_languages.get(user_id, self.default_language)
    
    def get_message(self, key: MessageKey, user_id: Optional[int] = None, 
                   language: Optional[Language] = None, **kwargs) -> str:
        """Get a localized message.
        
        Args:
            key: Message key to retrieve
            user_id: Telegram user ID (for language detection)
            language: Override language (if provided, ignores user_id)
            **kwargs: Variables to format into the message
            
        Returns:
            Formatted localized message
        """
        # Determine language to use
        if language is not None:
            lang = language
        elif user_id is not None:
            lang = self.get_user_language(user_id)
        else:
            lang = self.default_language
        
        # Get message template
        try:
            template = MESSAGES[lang][key]
        except KeyError:
            # Fallback to default language if key not found
            try:
                template = MESSAGES[self.default_language][key]
            except KeyError:
                return f"[Missing translation: {key}]"
        
        # Format template with provided variables
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError) as e:
            # Return template without formatting if error occurs
            return template
    
    def get_formatted_message(self, key: MessageKey, user_id: Optional[int] = None,
                            language: Optional[Language] = None, **kwargs) -> str:
        """Get a formatted message with line breaks and proper spacing.
        
        This is an alias for get_message but makes it clear that the message
        will be properly formatted for Telegram.
        
        Args:
            key: Message key to retrieve
            user_id: Telegram user ID (for language detection)
            language: Override language (if provided, ignores user_id)
            **kwargs: Variables to format into the message
            
        Returns:
            Formatted localized message
        """
        return self.get_message(key, user_id, language, **kwargs)
    
    def get_available_languages(self) -> list[Language]:
        """Get list of available languages.
        
        Returns:
            List of supported languages
        """
        return list(MESSAGES.keys())
    
    def detect_language_from_locale(self, locale: str) -> Language:
        """Detect language from Telegram user locale.
        
        Args:
            locale: Telegram user locale (e.g., 'en', 'ru', 'en-US')
            
        Returns:
            Detected language or default language
        """
        if not locale:
            return self.default_language
        
        # Extract language code (first part before '-')
        lang_code = locale.lower().split('-')[0]
        
        # Map to our supported languages
        if lang_code == 'ru':
            return Language.RU
        elif lang_code == 'en':
            return Language.EN
        else:
            return self.default_language


# Global instance
_i18n_manager: Optional[I18nManager] = None


def get_i18n_manager() -> I18nManager:
    """Get the global i18n manager instance.
    
    Returns:
        Global I18nManager instance
    """
    global _i18n_manager
    if _i18n_manager is None:
        _i18n_manager = I18nManager()
    return _i18n_manager


def init_i18n(default_language: Language = Language.EN) -> I18nManager:
    """Initialize the i18n system.
    
    Args:
        default_language: Default language to use
        
    Returns:
        Initialized I18nManager instance
    """
    global _i18n_manager
    _i18n_manager = I18nManager(default_language)
    return _i18n_manager