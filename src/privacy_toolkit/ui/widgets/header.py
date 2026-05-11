"""ARIVIM-style header widget with large block-font title."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Label, Static

from privacy_toolkit.core.constants import APP_VERSION

_TITLE = r"""
██████╗ ██████╗ ██╗██╗   ██╗ █████╗  ██████╗██╗   ██╗    ████████╗ ██████╗  ██████╗ ██╗     ██╗  ██╗██╗████████╗
██╔══██╗██╔══██╗██║██║   ██║██╔══██╗██╔════╝╚██╗ ██╔╝    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██║ ██╔╝██║╚══██╔══╝
██████╔╝██████╔╝██║╚██╗ ██╔╝███████║██║      ╚████╔╝        ██║   ██║   ██║██║   ██║██║     █████╔╝ ██║   ██║   
██╔═══╝ ██╔══██╗██║ ╚████╔╝ ██╔══██║██║       ╚██╔╝         ██║   ██║   ██║██║   ██║██║     ██╔═██╗ ██║   ██║   
██║     ██║  ██║██║  ╚██╔╝  ██║  ██║╚██████╗   ██║          ██║   ╚██████╔╝╚██████╔╝███████╗██║  ██╗██║   ██║   
╚═╝     ╚═╝  ╚═╝╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝   ╚═╝          ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝   ╚═╝ 
"""


class AppHeader(Static):
    """Top banner matching ARIVIM style."""

    DEFAULT_CSS = """
    AppHeader {
        height: auto;
        background: #0a0a0f;
        border: solid #00bcd4;
        padding: 0 2;
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label(
            "  Welcome to  [bold cyan]PRIVATE DATA CLEANUP TOOLKIT[/]",
            id="welcome-line",
        )
        yield Label(_TITLE.strip("\n"), id="ascii-title")
        yield Label(
            f"[bold green]Version: v{APP_VERSION}[/]",
            id="version-badge",
        )
        yield Label(
            "─── [dim]Personal Data Broker Tracking & Cleanup Command Center[/] ───",
            id="subtitle-line",
        )
