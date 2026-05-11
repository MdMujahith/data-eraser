"""Settings screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Label

from privacy_toolkit.ui.widgets.logs import LogPanel


def _row(label: str, value: object, sensitive: bool = False) -> str:
    val_str = "[dim]***[/]" if sensitive else f"[green]{value}[/]"
    return f"[dim]{label:<30}[/]  {val_str}"


class SettingsScreen(Screen):
    BINDINGS = [
        Binding("escape,q", "go_back", "Back"),
        Binding("v", "verify_network", "Verify Network"),
    ]

    def compose(self) -> ComposeResult:
        yield Label(
            "[bold cyan]── SETTINGS ─────────────────────────────────────────────────[/]",
            classes="screen-title",
        )
        yield Label(
            "[dim]  Read-only. Edit .env then restart. V = verify network. ESC = back.[/]",
            classes="back-hint",
        )
        yield Label(id="settings-content")
        yield LogPanel(id="settings-log")
        yield Footer()

    def on_mount(self) -> None:
        self._render()

    def _render(self) -> None:
        try:
            from privacy_toolkit.config.settings import get_settings
            from privacy_toolkit.db.database import health_check
            s = get_settings()
            db_ok = health_check()
            lines = [
                "[bold cyan]─ App ──────────────────────────────────────────[/]",
                _row("Environment", s.app_env),
                _row("Log Level", s.log_level),
                _row("Version", s.app_version),
                "",
                "[bold cyan]─ Database ─────────────────────────────────────[/]",
                _row("Database URL", s.database_url),
                _row("DB Health", "✓ ok" if db_ok else "✗ error"),
                "",
                "[bold cyan]─ Encryption ───────────────────────────────────[/]",
                _row("Encryption Key", "set" if s.encryption_key else "NOT SET", sensitive=bool(s.encryption_key)),
                _row("Keyring Service", s.keyring_service_name),
                "",
                "[bold cyan]─ Network / Proxy ──────────────────────────────[/]",
                _row("Proxy Mode", s.proxy_mode),
                _row("Proxy URL", s.proxy_url or "—"),
                _row("Tor Host:Port", f"{s.tor_socks_host}:{s.tor_socks_port}"),
                _row("Privacy Verify Enabled", s.privacy_verify_enabled),
                _row("Timeout (s)", s.request_timeout),
                _row("Retry Max", s.request_retry_max),
                _row("Rate Limit (req/min)", s.scan_rate_limit_per_minute),
                "",
                "[bold cyan]─ Scheduler ────────────────────────────────────[/]",
                _row("Scan Interval (days)", s.scheduler_interval_days),
                "",
                "[bold cyan]─ Opt-Out ──────────────────────────────────────[/]",
                _row("Auto Opt-Out Enabled", s.auto_optout_enabled),
                "",
                "[dim]  Edit .env → restart to apply changes.[/]",
            ]
            self.query_one("#settings-content", Label).update("\n".join(lines))
        except Exception as exc:
            self.query_one("#settings-log", LogPanel).error(str(exc))

    def action_verify_network(self) -> None:
        log = self.query_one("#settings-log", LogPanel)
        log.info("Running network verification…")
        try:
            from privacy_toolkit.config.settings import get_settings
            from privacy_toolkit.network.verifier import verify_current_route
            s = get_settings()
            route = verify_current_route(
                proxy_mode=s.proxy_mode,
                proxy_url=s.proxy_url,
                tor_host=s.tor_socks_host,
                tor_port=s.tor_socks_port,
                fail_closed=False,
            )
            log.success(
                f"mode={route.proxy_mode} proxy={route.proxy_active} tor={route.tor_confirmed}"
            )
            if route.warning:
                log.warning(route.warning)
        except Exception as exc:
            log.error(str(exc))

    def action_go_back(self) -> None:
        self.app.pop_screen()
