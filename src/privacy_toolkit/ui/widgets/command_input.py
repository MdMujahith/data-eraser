"""Bottom command input bar."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Input, Label, Static

COMMAND_MAP: dict[str, str] = {
    "1": "screen.brokers",
    "2": "screen.search",
    "3": "screen.categories",
    "4": "screen.scan",
    "5": "screen.optouts",
    "6": "screen.scheduler",
    "7": "screen.settings",
    "q": "app.quit",
    "quit": "app.quit",
    "exit": "app.quit",
    "brokers": "screen.brokers",
    "scan": "screen.scan",
    "optouts": "screen.optouts",
    "settings": "screen.settings",
    "help": "screen.help",
}

_HELP_TEXT = (
    "Commands: 1-7 navigate · scan · brokers · optouts · settings · help · q quit"
)


class CommandInput(Static):
    """► command prompt at the bottom of the dashboard."""

    DEFAULT_CSS = """
    CommandInput {
        height: 3;
        border-top: solid #00bcd4;
        background: #0a0a0a;
        layout: horizontal;
        padding: 0 2;
    }
    #cmd-prompt {
        color: #00bcd4;
        text-style: bold;
        width: 3;
        content-align: center middle;
    }
    #cmd-input {
        background: #0a0a0a;
        color: #00e5ff;
        border: none;
        width: 1fr;
    }
    #cmd-hint {
        color: #546e7a;
        width: 60;
        content-align: right middle;
    }
    """

    BINDINGS = [
        Binding("escape", "clear_input", "Clear"),
    ]

    def compose(self) -> ComposeResult:
        yield Label("►", id="cmd-prompt")
        yield Input(placeholder="enter command…", id="cmd-input")
        yield Label(_HELP_TEXT, id="cmd-hint")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip().lower()
        event.input.clear()
        if value:
            self.app.handle_command(value)

    def action_clear_input(self) -> None:
        self.query_one("#cmd-input", Input).clear()

    def focus_input(self) -> None:
        self.query_one("#cmd-input", Input).focus()
