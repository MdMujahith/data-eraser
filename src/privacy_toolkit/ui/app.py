"""Textual application entry point."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding

from privacy_toolkit.core.constants import APP_NAME, APP_VERSION
from privacy_toolkit.ui.theme import APP_CSS
from privacy_toolkit.ui.screens.dashboard import DashboardScreen
from privacy_toolkit.ui.screens.brokers import BrokersScreen
from privacy_toolkit.ui.screens.scans import ScansScreen
from privacy_toolkit.ui.screens.optouts import OptOutsScreen
from privacy_toolkit.ui.screens.settings import SettingsScreen


class PrivacyToolkitApp(App):
    """Root Textual application for the Privacy Toolkit."""

    TITLE = f"{APP_NAME} v{APP_VERSION}"
    CSS = APP_CSS
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False),
    ]

    SCREENS = {
        "dashboard": DashboardScreen,
        "brokers": BrokersScreen,
        "scans": ScansScreen,
        "optouts": OptOutsScreen,
        "settings": SettingsScreen,
    }

    def on_mount(self) -> None:
        self.push_screen("dashboard")

    def handle_command(self, command: str) -> None:
        """Dispatch a command string from the command-input widget."""
        cmd = command.strip().lower()
        routes: dict[str, str] = {
            "1": "brokers",
            "brokers": "brokers",
            "2": "scans",
            "search": "scans",
            "3": "brokers",
            "categories": "brokers",
            "4": "scans",
            "scan": "scans",
            "5": "optouts",
            "optouts": "optouts",
            "6": "settings",
            "scheduler": "settings",
            "7": "settings",
            "settings": "settings",
        }
        if cmd in ("q", "quit", "exit"):
            self.exit()
            return
        if cmd == "help":
            self._show_help()
            return
        target = routes.get(cmd)
        if target:
            self.push_screen(target)
        else:
            try:
                dashboard = self.get_screen("dashboard")
                dashboard.log_info(f"Unknown command: {cmd!r}. Type 'help' for commands.")
            except Exception:
                pass

    def _show_help(self) -> None:
        help_text = (
            "Commands: 1=Brokers  2=Search  3=Categories  4=Scan  "
            "5=Opt-Outs  6=Scheduler  7=Settings  q=Quit"
        )
        try:
            self.get_screen("dashboard").log_info(help_text)
        except Exception:
            pass
