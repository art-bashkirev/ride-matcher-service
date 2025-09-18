from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from config.settings import get_config

class TelegramSettings(BaseModel):
    token: Optional[str]
    parse_mode: str = "HTML"
    enabled: bool = True

    @classmethod
    def load(cls) -> "TelegramSettings":
        cfg = get_config()
        return cls(token=cfg.telegram_bot_token, enabled=bool(cfg.telegram_bot_token))

__all__ = ["TelegramSettings"]
