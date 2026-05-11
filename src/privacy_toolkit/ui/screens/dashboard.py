"""ARIVIM-style dashboard screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Input, Label, Static

from privacy_toolkit.core.constants import APP_VERSION, Status
from privacy_toolkit.ui.widgets.header import AppHeader
from privacy_toolkit.ui.widgets.logs import LogPanel
from privacy_toolkit.ui.widgets.menu import MainMenu
from privacy_toolkit.ui.widgets.overview import OverviewPanel


class _StatusBar(Static):
    DEFAULT_CSS = """
    _StatusBar {
        height: 1;
        background: #050510;
        padding: 0 2;
        border-bottom: solid #00bcd4;
        border-top: solid #00bcd4;
    }
    """
    def __init__(self, **kw: object) -> None:
        super().__init__(**kw)
        self._brokers = 0; self._cats = 0
        self._db = False; self._net = "Direct"; self._ver = False

    def on_mount(self) -> None: self._refresh()

    def _refresh(self) -> None:
        try:
            from privacy_toolkit.db.database import get_db, health_check
            from privacy_toolkit.db.repository import BrokerRepository
            with get_db() as db:
                r = BrokerRepository(db)
                self._brokers = r.count(); self._cats = len(r.categories())
            self._db = health_check()
        except Exception:
            self._db = False
        db_s  = "[green]OK[/]"  if self._db  else "[red]ERR[/]"
        net_s = (f"[green]{self._net} ✓[/]"
                 if self._ver else f"[yellow]{self._net}[/]")
        self.update(
            f" [bold #7c4dff on #1a0035] PRIVACY [/]  "
            f"[dim cyan]v{APP_VERSION}[/]  [#37474f]│[/]  "
            f"[cyan]{self._brokers}[/] [dim]Brokers[/]  [#37474f]│[/]  "
            f"[cyan]{self._cats}[/] [dim]Categories[/]  [#37474f]│[/]  "
            f"[dim]DB:[/] {db_s}  [#37474f]│[/]  "
            f"[dim]Network:[/] {net_s}"
        )

    def set_network(self, label: str, verified: bool) -> None:
        self._net = label; self._ver = verified; self._refresh()


class _QuickLinks(Static):
    DEFAULT_CSS = """
    _QuickLinks {
        height: 3;
        background: #050510;
        border: solid #00bcd4;
        margin: 0 1;
        padding: 0 3;
        content-align: left middle;
    }
    """
    def __init__(self, **kw: object) -> None:
        super().__init__(**kw)
        self._c = {"Email":0,"Phone":0,"Address":0,"Brokers":0,"Manual":0,"Done":0}

    def on_mount(self) -> None: self._refresh()

    def _refresh(self) -> None:
        try:
            from privacy_toolkit.db.database import get_db
            from privacy_toolkit.db.repository import BrokerRepository, OptOutRequestRepository
            with get_db() as db:
                b = BrokerRepository(db); o = OptOutRequestRepository(db)
                self._c["Brokers"] = b.count()
                self._c["Manual"]  = o.count_manual_review()
                self._c["Done"]    = o.count_by_status(Status.COMPLETED)
        except Exception:
            pass
        icons = {"Email":"📧","Phone":"📱","Address":"🏠","Brokers":"🗄","Manual":"⚠","Done":"✅"}
        parts = "  ".join(
            f"{icons.get(k,'•')} [bold cyan]{k}[/]([green]{v}[/])"
            for k,v in self._c.items()
        )
        self.update(f"  {parts}")


class _ShortcutBar(Static):
    DEFAULT_CSS = """
    _ShortcutBar {
        height: 1;
        background: #050510;
        border-top: solid #1a3a4a;
        padding: 0 2;
        content-align: left middle;
    }
    """
    def compose(self) -> ComposeResult:
        yield Label(
            "[cyan][1][/][dim] Browse[/]  "
            "[cyan][2][/][dim] Search[/]  "
            "[cyan][3][/][dim] Category[/]  "
            "[cyan][4][/][dim] Scan[/]  "
            "[cyan][5][/][dim] Opt-Outs[/]  "
            "[cyan][6][/][dim] Scheduler[/]  "
            "[cyan][7][/][dim] Settings[/]  "
            "[cyan][Q][/][dim] Quit[/]"
        )


class _CmdBar(Static):
    DEFAULT_CSS = """
    _CmdBar {
        height: 3;
        background: #0a0a0f;
        border: solid #00bcd4;
        margin: 0 1;
        layout: horizontal;
        padding: 0 1;
    }
    #cmd-prompt { color: #00bcd4; text-style: bold; width: 4; content-align: center middle; }
    #cmd-input  { background: #0a0a0f; color: #00e5ff; border: none; width: 1fr; }
    #cmd-input:focus { background: #0d1f2d; border: none; }
    """
    def compose(self) -> ComposeResult:
        yield Label("> ", id="cmd-prompt")
        yield Input(placeholder="enter command or number…", id="cmd-input")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip().lower()
        event.input.clear()
        if val:
            self.app.handle_command(val)

    def focus_input(self) -> None:
        self.query_one("#cmd-input", Input).focus()


class DashboardScreen(Screen):
    """Root ARIVIM-style dashboard."""

    BINDINGS = [
        Binding("1", "nav_brokers",   "Brokers",    show=False),
        Binding("2", "nav_scan",      "Search",     show=False),
        Binding("3", "nav_brokers",   "Categories", show=False),
        Binding("4", "nav_scan",      "Scan",       show=False),
        Binding("5", "nav_optouts",   "Opt-Outs",   show=False),
        Binding("6", "nav_settings",  "Scheduler",  show=False),
        Binding("7", "nav_settings",  "Settings",   show=False),
        Binding("r", "refresh",       "Refresh",    show=False),
        Binding("q", "quit_app",      "Quit",       show=False),
    ]

    def compose(self) -> ComposeResult:
        yield AppHeader(id="app-header")
        yield _StatusBar(id="status-bar")
        with Static(id="body"):
            yield MainMenu(id="menu-panel")
            yield OverviewPanel(id="overview-panel")
        yield _QuickLinks(id="quick-links")
        yield _ShortcutBar(id="shortcut-bar")
        yield _CmdBar(id="cmd-bar")
        yield LogPanel(id="dash-log")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(_CmdBar).focus_input()
        self.log_msg("Privacy Toolkit ready. Type a number or command.")

    def log_msg(self, msg: str, level: str = "info") -> None:
        try:
            self.query_one("#dash-log", LogPanel).write(msg, level)
        except Exception:
            pass

    def action_refresh(self) -> None:
        try:
            self.query_one(OverviewPanel).refresh_stats()
            self.query_one(_StatusBar)._refresh()
            self.query_one(_QuickLinks)._refresh()
            self.log_msg("Stats refreshed.")
        except Exception:
            pass

    def action_nav_brokers(self)  -> None: self.app.push_screen("brokers")
    def action_nav_scan(self)     -> None: self.app.push_screen("scans")
    def action_nav_optouts(self)  -> None: self.app.push_screen("optouts")
    def action_nav_settings(self) -> None: self.app.push_screen("settings")
    def action_quit_app(self)     -> None: self.app.exit()
