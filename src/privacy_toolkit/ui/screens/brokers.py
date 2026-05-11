"""Brokers list screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, Static

from privacy_toolkit.ui.widgets.logs import LogPanel
from privacy_toolkit.ui.widgets.status_table import BrokersTable


class BrokersScreen(Screen):
    BINDINGS = [
        Binding("escape,q", "go_back", "Back"),
        Binding("r", "reload", "Reload"),
    ]

    def compose(self) -> ComposeResult:
        yield Label(
            "[bold cyan]── BROKER REGISTRY ──────────────────────────────────────────[/]",
            classes="screen-title",
        )
        yield Label("[dim]  ESC / Q = back   R = reload[/]", classes="back-hint")
        with Static(id="broker-controls"):
            yield Button("↺  Reload", id="btn-reload")
        yield BrokersTable(id="brokers-table")
        yield LogPanel(id="brokers-log")
        yield Footer()

    def on_mount(self) -> None:
        self._load()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-reload":
            self._load()

    def _load(self) -> None:
        log = self.query_one("#brokers-log", LogPanel)
        try:
            from privacy_toolkit.db.database import get_db
            from privacy_toolkit.db.repository import BrokerRepository
            with get_db() as db:
                broker_list = BrokerRepository(db).list_enabled()
            self.query_one("#brokers-table", BrokersTable).populate(broker_list)
            log.info(f"Loaded {len(broker_list)} enabled brokers.")
        except Exception as exc:
            log.error(f"Failed to load brokers: {exc}")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_reload(self) -> None:
        self._load()
