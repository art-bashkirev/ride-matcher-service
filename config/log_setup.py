import logging
import sys
from typing import Optional

from .settings import get_config

_LOGGER_CACHE: dict[str, logging.Logger] = {}


def _configure_root_once():
    if getattr(_configure_root_once, "_configured", False):  # type: ignore[attr-defined]
        return
    cfg = get_config()
    level = getattr(logging, cfg.normalized_log_level, logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(level)

    # Suppress httpx logging
    logging.getLogger("httpx").setLevel(logging.WARNING)

    _configure_root_once._configured = True  # type: ignore[attr-defined]


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a configured logger with caching.

    Ensures root logger is configured once; returns child loggers subsequently.
    """
    _configure_root_once()
    lname = name or "app"
    if lname not in _LOGGER_CACHE:
        _LOGGER_CACHE[lname] = logging.getLogger(lname)
    return _LOGGER_CACHE[lname]
