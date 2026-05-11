"""Opt-out queue screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, Static

from privacy_toolkit.ui.widgets.logs import LogPanel
from privacy_toolkit.ui.widgets.status_table import OptOutTable


class OptOutsScreen(Screen):
    BINDINGS = [
        Binding("escape,q", "go_back", "Back"),
        Binding("r", "reload", "Reload"),
    ]

    def compose(self) -> ComposeResult:
        yield Label(
            "[bold cyan]── OPT-OUT QUEUE ────────────────────────────────────────────[/]",
            classes="screen-title",
        )
        yield Label(
            "[dim]  Active opt-out requests.  Use CLI: privacy-toolkit optouts --finding <id>  ESC = back[/]",
            classes="back-hint",
        )
        with Static(id="optout-controls"):
            yield Button("↺  Reload", id="btn-reload")
        yield OptOutTable(id="optout-table")
        yield LogPanel(id="optout-log")
        yield Footer()

    def on_mount(self) -> None:
        self._load()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-reload":
            self._load()

    def _load(self) -> None:
        log = self.query_one("#optout-log", LogPanel)
        try:
            from privacy_toolkit.db.database import get_db
            from privacy_toolkit.db.repository import OptOutRequestRepository
            with get_db() as db:
                requests = OptOutRequestRepository(db).list_active()
            self.query_one("#optout-table", OptOutTable).populate(requests)
            log.info(f"Loaded {len(requests)} active opt-out requests.")
        except Exception as exc:
            log.error(str(exc))

    def action_reload(self) -> None:
        self._load()

    def action_go_back(self) -> None:
        self.app.pop_screen()
