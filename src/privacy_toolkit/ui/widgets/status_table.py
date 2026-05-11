"""Reusable DataTable widget for displaying findings / opt-out requests."""

from __future__ import annotations

from typing import Sequence

from textual.widgets import DataTable


def _status_markup(status: str) -> str:
    _COLOURS: dict[str, str] = {
        "FOUND": "yellow",
        "NOT_FOUND": "green",
        "COMPLETED": "green",
        "FAILED": "red",
        "MANUAL_REVIEW_REQUIRED": "red",
        "MANUAL_CAPTCHA_REQUIRED": "red",
        "EMAIL_VERIFICATION_REQUIRED": "yellow",
        "REQUEST_SENT": "cyan",
        "REQUEST_READY": "cyan",
        "SCANNING": "bright_cyan",
        "NOT_STARTED": "dim",
        "RESCAN_REQUIRED": "yellow",
    }
    colour = _COLOURS.get(status, "white")
    return f"[{colour}]{status}[/]"


class FindingsTable(DataTable):
    """DataTable pre-configured for BrokerFinding rows."""

    def on_mount(self) -> None:
        self.add_columns("ID", "Broker", "Status", "Found At", "Snippet")
        self.cursor_type = "row"

    def populate(self, findings: Sequence[object]) -> None:
        self.clear()
        for f in findings:
            self.add_row(
                str(f.id),  # type: ignore[attr-defined]
                f.broker.name if f.broker else "—",  # type: ignore[attr-defined]
                _status_markup(f.status),  # type: ignore[attr-defined]
                f.found_at.strftime("%Y-%m-%d %H:%M") if f.found_at else "—",  # type: ignore[attr-defined]
                (f.snippet or "")[:60],  # type: ignore[attr-defined]
            )


class OptOutTable(DataTable):
    """DataTable pre-configured for OptOutRequest rows."""

    def on_mount(self) -> None:
        self.add_columns("ID", "Broker", "Status", "Method", "Updated")
        self.cursor_type = "row"

    def populate(self, requests: Sequence[object]) -> None:
        self.clear()
        for r in requests:
            self.add_row(
                str(r.id),  # type: ignore[attr-defined]
                r.broker.name if r.broker else "—",  # type: ignore[attr-defined]
                _status_markup(r.status),  # type: ignore[attr-defined]
                r.method,  # type: ignore[attr-defined]
                r.updated_at.strftime("%Y-%m-%d %H:%M") if r.updated_at else "—",  # type: ignore[attr-defined]
            )


class BrokersTable(DataTable):
    """DataTable for Broker registry display."""

    def on_mount(self) -> None:
        self.add_columns("ID", "Name", "Category", "Auto Search", "Auto Opt-Out", "Enabled")
        self.cursor_type = "row"

    def populate(self, brokers: Sequence[object]) -> None:
        self.clear()
        for b in brokers:
            self.add_row(
                str(b.id),  # type: ignore[attr-defined]
                b.name,  # type: ignore[attr-defined]
                b.category,  # type: ignore[attr-defined]
                "[green]Yes[/]" if b.automated_search_allowed else "[dim]No[/]",  # type: ignore[attr-defined]
                "[green]Yes[/]" if b.automated_optout_allowed else "[dim]No[/]",  # type: ignore[attr-defined]
                "[green]✓[/]" if b.enabled else "[red]✗[/]",  # type: ignore[attr-defined]
            )
