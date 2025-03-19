"""Configuration package initialization."""

from . import settings

def initialize_with_console(console=None):
    """Initialize settings with an optional console reference."""
    if console:
        settings.set_console(console)
    settings.initialize_paths()
