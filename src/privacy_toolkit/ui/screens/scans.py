"""Scan screen — fixed threading + live progress."""

from __future__ import annotations

import threading

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, Static

from privacy_toolkit.ui.widgets.logs import LogPanel
from privacy_toolkit.ui.widgets.status_table import FindingsTable


class ScansScreen(Screen):
    BINDINGS = [
        Binding("escape,q", "go_back", "Back"),
        Binding("s",        "start_scan",      "Scan"),
        Binding("r",        "reload_findings", "Reload"),
    ]

    _scan_running: bool = False

    def compose(self) -> ComposeResult:
        yield Label(
            "[bold cyan]── RUN SCAN / FINDINGS ──────────────────────────────────────[/]",
            classes="screen-title",
        )
        yield Label(
            "[dim]  S = start scan  R = reload findings  ESC = back[/]",
            classes="back-hint",
        )
        with Static(id="scan-controls"):
            yield Button("▶  Start Scan", id="btn-scan", variant="primary")
            yield Button("↺  Reload Findings", id="btn-reload")
        yield Label("[dim]Ready.[/]", id="scan-status")
        yield FindingsTable(id="findings-table")
        yield LogPanel(id="scan-log")
        yield Footer()

    def on_mount(self) -> None:
        self._load_findings()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-scan":
            self.action_start_scan()
        elif event.button.id == "btn-reload":
            self._load_findings()

    def action_start_scan(self) -> None:
        if self._scan_running:
            self._log("Scan already in progress…", "warning")
            return
        self._scan_running = True
        self._set_status("[yellow]● Scanning…[/]")
        self._log("Scan started.")
        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self) -> None:
        try:
            from privacy_toolkit.recon.scanner import Scanner

            def cb(msg: str, cur: int, total: int) -> None:
                self.call_from_thread(self._set_status,
                    f"[cyan]{msg}[/]" + (f" ({cur}/{total})" if total else ""))
                self.call_from_thread(self._log, msg)

            summary = Scanner(progress_callback=cb).run()
            self.call_from_thread(self._scan_done, summary)
        except Exception as exc:
            self.call_from_thread(self._scan_error, str(exc))

    def _set_status(self, markup: str) -> None:
        try:
            self.query_one("#scan-status", Label).update(markup)
        except Exception:
            pass

    def _log(self, msg: str, level: str = "info") -> None:
        try:
            self.query_one("#scan-log", LogPanel).write(msg, level)
        except Exception:
            pass

    def _scan_done(self, summary: dict) -> None:
        self._scan_running = False
        if summary.get("aborted"):
            err = summary.get("error", "unknown error")
            self._set_status(f"[red]✗ Aborted:[/] {err}")
            self._log(f"Scan aborted: {err}", "error")
        else:
            f = summary.get("findings", 0)
            b = summary.get("brokers_scanned", 0)
            sk = summary.get("skipped", 0)
            self._set_status(
                f"[green]✓ Complete[/]  "
                f"findings=[yellow]{f}[/]  "
                f"brokers=[cyan]{b}[/]  "
                f"skipped=[dim]{sk}[/]"
            )
            self._log(f"Scan #{summary.get('scan_run_id')} complete. "
                      f"Findings: {f} / Brokers: {b} / Skipped: {sk}", "success")
            self._load_findings()

    def _scan_error(self, error: str) -> None:
        self._scan_running = False
        self._set_status(f"[red]✗ Error:[/] {error}")
        self._log(error, "error")

    def _load_findings(self) -> None:
        try:
            from privacy_toolkit.db.database import get_db
            from privacy_toolkit.db.repository import BrokerFindingRepository
            with get_db() as db:
                rows = BrokerFindingRepository(db).list_by_status("FOUND")
                rows2 = BrokerFindingRepository(db).list_by_status("MANUAL_REVIEW_REQUIRED")
            all_rows = list(rows) + list(rows2)
            self.query_one("#findings-table", FindingsTable).populate(all_rows)
            self._log(f"Loaded {len(all_rows)} findings.")
        except Exception as exc:
            self._log(str(exc), "error")

    def action_reload_findings(self) -> None:
        self._load_findings()

    def action_go_back(self) -> None:
        self.app.pop_screen()
