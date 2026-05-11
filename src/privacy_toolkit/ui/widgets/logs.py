"""Scrollable log panel widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Label, RichLog, Static


class LogPanel(Static):
    """Scrollable event/log display at the bottom of screens."""

    DEFAULT_CSS = """
    LogPanel {
        height: 8;
        border: solid #1a237e;
        background: #010d18;
        margin: 0 1;
    }
    LogPanel Label {
        color: #546e7a;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("[dim cyan]── LOG ──────────────────────────────────────[/]")
        yield RichLog(id="log-output", highlight=True, markup=True, max_lines=200)

    def write(self, message: str, level: str = "info") -> None:
        colours = {
            "info": "cyan",
            "success": "green",
            "warning": "yellow",
            "error": "red",
        }
        colour = colours.get(level, "white")
        try:
            log = self.query_one("#log-output", RichLog)
            log.write(f"[{colour}]{message}[/]")
        except Exception:
            pass

    def info(self, msg: str) -> None:
        self.write(msg, "info")

    def success(self, msg: str) -> None:
        self.write(msg, "success")

    def warning(self, msg: str) -> None:
        self.write(msg, "warning")

    def error(self, msg: str) -> None:
        self.write(msg, "error")
