"""Application bootstrap — initialise DB, logging, and return the TUI app."""

from __future__ import annotations

from typing import Optional

from privacy_toolkit.core.logging import configure_root, get_logger

logger = get_logger(__name__)


def bootstrap(log_level: Optional[str] = None) -> None:
    """Initialise settings, logging, and database.

    Call once at process start before launching the TUI or running CLI commands.
    """
    from privacy_toolkit.config.settings import get_settings
    settings = get_settings()

    level = log_level or settings.log_level
    configure_root(level)
    logger.debug("Bootstrap: log_level=%s", level)

    from privacy_toolkit.db.database import init_db
    init_db(settings.database_url)
    logger.debug("Bootstrap: database initialised at %s", settings.database_url)


def create_tui_app():
    """Bootstrap and return the Textual application instance."""
    bootstrap()
    from privacy_toolkit.ui.app import PrivacyToolkitApp
    return PrivacyToolkitApp()
