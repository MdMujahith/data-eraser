"""ARIVIM-style main menu widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Label, Static

_ITEMS: list[tuple[str, str, str]] = [
    ("[1]", "Browse Brokers",   "View & manage all broker configs and statuses"),
    ("[2]", "Search",           "Find findings by name, email, phone, or broker"),
    ("[3]", "Categories",       "Filter brokers by category"),
    ("[4]", "Run Scan",         "Start a privacy-verified scan now"),
    ("[5]", "Opt-Out Queue",    "View & action removal requests"),
    ("[6]", "Scheduler",        "Manage recurring scans"),
    ("[7]", "Settings",         "Proxy, Tor, DB, encryption, profile"),
    ("[Q]", "Quit",             "Exit toolkit"),
]


class MainMenu(Static):
    """Left panel — ARIVIM-style numbered menu."""

    DEFAULT_CSS = """
    MainMenu {
        border: solid #00bcd4;
        background: #0a0a0f;
        padding: 1 2;
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label(
            "── [bold cyan]MAIN MENU[/] " + "─" * 44,
            classes="panel-title",
        )
        yield Label("")
        for key, label, desc in _ITEMS:
            yield Label(
                f"  [bold cyan]{key:<5}[/]  [bold #e0f7fa]{label:<22}[/]  [#37474f]{desc}[/]",
                classes="menu-row",
            )
        yield Label("")
        yield Label(
            "  [dim]Type a number or command at the  >[/]  [dim cyan]prompt below[/]",
        )
