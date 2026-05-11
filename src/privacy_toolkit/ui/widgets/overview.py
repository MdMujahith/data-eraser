"""ARIVIM-style overview panel."""

from __future__ import annotations

import platform
import sys

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Label, Static

from privacy_toolkit.core.constants import Status


class OverviewPanel(Static):
    """Right panel — live stats in ARIVIM style."""

    broker_count:    reactive[int]  = reactive(0)
    category_count:  reactive[int]  = reactive(0)
    findings_count:  reactive[int]  = reactive(0)
    optout_count:    reactive[int]  = reactive(0)
    completed_count: reactive[int]  = reactive(0)
    manual_count:    reactive[int]  = reactive(0)
    db_ok:           reactive[bool] = reactive(False)
    net_label:       reactive[str]  = reactive("Direct")
    net_verified:    reactive[bool] = reactive(False)

    DEFAULT_CSS = """
    OverviewPanel {
        border: solid #00bcd4;
        background: #0a0a0f;
        padding: 1 2;
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("── [bold cyan]OVERVIEW[/] " + "─" * 28, classes="panel-title")
        yield Label("")
        for wid in [
            "ov-brokers","ov-categories","ov-findings",
            "ov-optouts","ov-completed","ov-manual",
            "ov-sep","ov-config","ov-platform","ov-network",
        ]:
            yield Label("", id=wid)

    def on_mount(self) -> None:
        self.refresh_stats()

    def refresh_stats(self) -> None:
        try:
            from privacy_toolkit.db.database import get_db, health_check
            from privacy_toolkit.db.repository import (
                BrokerRepository, BrokerFindingRepository, OptOutRequestRepository,
            )
            with get_db() as db:
                br = BrokerRepository(db)
                fr = BrokerFindingRepository(db)
                or_ = OptOutRequestRepository(db)
                self.broker_count    = br.count()
                self.category_count  = len(br.categories())
                self.findings_count  = (fr.count_by_status(Status.FOUND)
                                        + fr.count_by_status(Status.MANUAL_REVIEW_REQUIRED))
                self.optout_count    = len(or_.list_active())
                self.completed_count = or_.count_by_status(Status.COMPLETED)
                self.manual_count    = or_.count_manual_review()
                self.db_ok           = health_check()
        except Exception:
            self.db_ok = False
        self._paint()

    def _paint(self) -> None:
        py      = f"py{sys.version_info.major}.{sys.version_info.minor}"
        os_name = platform.system()
        db_s    = "[green]√ ok[/]" if self.db_ok else "[red]✗ error[/]"
        net_s   = (f"[green]{self.net_label} ✓[/]"
                   if self.net_verified else f"[yellow]{self.net_label}[/]")

        def row(label: str, val: object, style: str = "green") -> str:
            return f"  [#546e7a]{label:<18}[/]  [{style}]{val}[/]"

        updates = {
            "ov-brokers":    row("Brokers",       self.broker_count),
            "ov-categories": row("Categories",    self.category_count),
            "ov-findings":   row("Findings",      self.findings_count,
                                 "yellow" if self.findings_count else "green"),
            "ov-optouts":    row("Opt-Out Requests", self.optout_count,
                                 "yellow" if self.optout_count else "green"),
            "ov-completed":  row("Completed",     self.completed_count),
            "ov-manual":     row("Manual Review", self.manual_count,
                                 "red" if self.manual_count else "green"),
            "ov-sep":        "  [#1a3a4a]" + "─" * 32 + "[/]",
            "ov-config":     f"  [#546e7a]{'Config':<18}[/]  {db_s}",
            "ov-platform":   row("Platform", f"{os_name} · {py}"),
            "ov-network":    f"  [#546e7a]{'Network':<18}[/]  {net_s}",
        }
        for wid, markup in updates.items():
            try:
                self.query_one(f"#{wid}", Label).update(markup)
            except Exception:
                pass

    def watch_broker_count(self, _: int)  -> None: self._paint()
    def watch_db_ok(self, _: bool)        -> None: self._paint()
    def watch_net_verified(self, _: bool) -> None: self._paint()
