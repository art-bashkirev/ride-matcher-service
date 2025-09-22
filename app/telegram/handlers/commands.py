"""Legacy command handlers file - now imports from individual command modules."""
from __future__ import annotations

from .commands.start import cmd_start
from .commands.help import cmd_help
from .commands.schedule import cmd_schedule
from .commands.search import cmd_search
from .commands.thread import cmd_thread
from .commands.carrier import cmd_carrier
from .commands.copyright import cmd_copyright
from .commands.echo import echo_text

__all__ = [
    "cmd_start",
    "cmd_help",
    "cmd_schedule", 
    "cmd_search",
    "cmd_thread",
    "cmd_carrier",
    "cmd_copyright",
    "echo_text"
]
