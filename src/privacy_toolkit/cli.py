"""Typer CLI entrypoints."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from privacy_toolkit.core.constants import APP_NAME, APP_VERSION

app = typer.Typer(
    name="privacy-toolkit",
    help=f"{APP_NAME} v{APP_VERSION} — Personal data broker tracking & cleanup.",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


def _bootstrap() -> None:
    from privacy_toolkit.app import bootstrap
    bootstrap()


# ── tui ───────────────────────────────────────────────────────────────────────

@app.command()
def tui() -> None:
    """Launch the interactive TUI dashboard."""
    _bootstrap()
    from privacy_toolkit.app import create_tui_app
    tui_app = create_tui_app()
    tui_app.run()


# ── init ──────────────────────────────────────────────────────────────────────

@app.command()
def init(
    generate_key: bool = typer.Option(False, "--generate-key", help="Generate a new Fernet encryption key."),
    store_in_keyring: bool = typer.Option(False, "--keyring", help="Store key in OS keyring instead of printing."),
) -> None:
    """Initialise the database and optionally generate an encryption key."""
    _bootstrap()
    console.print(Panel(f"[bold cyan]{APP_NAME}[/] — Init", border_style="cyan"))

    from privacy_toolkit.db.database import health_check
    if health_check():
        console.print("[green]✓ Database ready.[/]")
    else:
        console.print("[red]✗ Database error.[/]")
        raise typer.Exit(1)

    if generate_key:
        from privacy_toolkit.security.encryption import generate_key as gen_key
        key = gen_key()
        if store_in_keyring:
            from privacy_toolkit.config.settings import get_settings
            from privacy_toolkit.security.secrets import store_secret
            s = get_settings()
            from privacy_toolkit.core.constants import KEYRING_SERVICE, KEYRING_USERNAME
            ok = store_secret(KEYRING_SERVICE, KEYRING_USERNAME, key)
            if ok:
                console.print("[green]✓ Encryption key stored in OS keyring.[/]")
            else:
                console.print("[yellow]⚠ Keyring unavailable — add key to .env manually.[/]")
                console.print(f"[bold]ENCRYPTION_KEY=[/]{key}")
        else:
            console.print(f"\n[bold yellow]Add this to your .env:[/]\nENCRYPTION_KEY={key}\n")
            console.print("[red]⚠ Store this key securely — losing it means losing all encrypted data.[/]")

    console.print("[green]✓ Init complete.[/]")


# ── scan ──────────────────────────────────────────────────────────────────────

@app.command()
def scan(
    profile: str = typer.Option("default", "--profile", "-p", help="Profile label to scan."),
) -> None:
    """Run a privacy scan across all enabled brokers."""
    _bootstrap()
    from privacy_toolkit.recon.scanner import Scanner

    console.print(Panel("[bold cyan]Running Privacy Scan[/]", border_style="cyan"))

    def progress(msg: str, cur: int, total: int) -> None:
        suffix = f" ({cur}/{total})" if total else ""
        console.print(f"  [cyan]{msg}[/]{suffix}")

    scanner = Scanner(profile_label=profile, progress_callback=progress)
    summary = scanner.run()

    if summary.get("aborted"):
        console.print(f"[red]✗ Scan aborted: {summary.get('error')}[/]")
        raise typer.Exit(1)

    console.print(
        f"\n[green]✓ Scan #{summary['scan_run_id']} complete.[/] "
        f"Findings: [yellow]{summary['findings']}[/] / "
        f"Brokers: [cyan]{summary['brokers_scanned']}[/]"
    )


# ── brokers ───────────────────────────────────────────────────────────────────

@app.command()
def brokers() -> None:
    """List all registered brokers."""
    _bootstrap()
    from privacy_toolkit.db.database import get_db
    from privacy_toolkit.db.repository import BrokerRepository

    with get_db() as db:
        rows = BrokerRepository(db).list_enabled()

    tbl = Table(title="Registered Brokers", border_style="cyan", header_style="bold cyan")
    tbl.add_column("ID", style="dim", width=5)
    tbl.add_column("Name")
    tbl.add_column("Category")
    tbl.add_column("Auto Search")
    tbl.add_column("Auto Opt-Out")

    for b in rows:
        tbl.add_row(
            str(b.id), b.name, b.category,
            "[green]yes[/]" if b.automated_search_allowed else "[dim]no[/]",
            "[green]yes[/]" if b.automated_optout_allowed else "[dim]no[/]",
        )
    console.print(tbl)


# ── optouts ───────────────────────────────────────────────────────────────────

@app.command()
def optouts(
    finding_id: Optional[int] = typer.Option(None, "--finding", "-f", help="Initiate opt-out for a finding ID."),
) -> None:
    """View opt-out queue or initiate an opt-out."""
    _bootstrap()
    from privacy_toolkit.db.database import get_db
    from privacy_toolkit.db.repository import OptOutRequestRepository

    if finding_id is not None:
        from privacy_toolkit.optout.workflow import OptOutWorkflow
        result = OptOutWorkflow().initiate(finding_id)
        console.print(f"[bold]Status:[/] {result.status}")
        console.print(f"[bold]Message:[/] {result.message}")
        if result.manual_steps:
            console.print("\n[bold cyan]Manual Steps:[/]")
            for step in result.manual_steps:
                console.print(f"  {step}")
        return

    with get_db() as db:
        rows = OptOutRequestRepository(db).list_active()

    tbl = Table(title="Active Opt-Out Requests", border_style="cyan", header_style="bold cyan")
    tbl.add_column("ID", style="dim", width=5)
    tbl.add_column("Broker")
    tbl.add_column("Status")
    tbl.add_column("Method")

    for r in rows:
        tbl.add_row(
            str(r.id),
            r.broker.name if r.broker else "—",
            r.status,
            r.method,
        )
    console.print(tbl)


# ── verify-network ────────────────────────────────────────────────────────────

@app.command(name="verify-network")
def verify_network() -> None:
    """Verify current network route / proxy status."""
    _bootstrap()
    from privacy_toolkit.config.settings import get_settings
    from privacy_toolkit.network.verifier import verify_current_route

    s = get_settings()
    console.print(Panel("[bold cyan]Network Route Verification[/]", border_style="cyan"))

    try:
        route = verify_current_route(
            proxy_mode=s.proxy_mode,
            proxy_url=s.proxy_url,
            tor_host=s.tor_socks_host,
            tor_port=s.tor_socks_port,
            fail_closed=False,
        )
        console.print(f"[bold]Proxy Mode:[/]     {route.proxy_mode}")
        console.print(f"[bold]Proxy Active:[/]   {'[green]yes[/]' if route.proxy_active else '[yellow]no[/]'}")
        console.print(f"[bold]Tor Confirmed:[/]  {'[green]yes[/]' if route.tor_confirmed else '[dim]no[/]'}")
        console.print(f"[bold]Public IP:[/]      [dim][REDACTED][/]")
        if route.warning:
            console.print(f"[bold yellow]⚠ Warning:[/] {route.warning}")
    except Exception as exc:
        console.print(f"[red]✗ Verification error: {exc}[/]")
        raise typer.Exit(1)


# ── db seed ───────────────────────────────────────────────────────────────────

@app.command(name="db")
def db_cmd(
    action: str = typer.Argument("seed", help="Action: seed"),
) -> None:
    """Database management commands."""
    _bootstrap()
    if action == "seed":
        from privacy_toolkit.db.seed import seed_brokers, seed_demo_profile
        count = seed_brokers()
        seed_demo_profile()
        console.print(f"[green]✓ Seeded {count} brokers and demo profile.[/]")
    else:
        console.print(f"[red]Unknown action: {action!r}. Available: seed[/]")
        raise typer.Exit(1)


# ── scheduler ─────────────────────────────────────────────────────────────────

@app.command()
def scheduler(
    action: str = typer.Argument("start", help="Action: start | stop | status | trigger"),
) -> None:
    """Manage the background scan scheduler."""
    _bootstrap()
    from privacy_toolkit.scheduler.runner import (
        get_job_status, start_scheduler, stop_scheduler, trigger_scan_now
    )
    if action == "start":
        start_scheduler()
        console.print("[green]✓ Scheduler started.[/]")
        status = get_job_status()
        console.print(f"Next run: {status.get('next_run', '—')}")
    elif action == "stop":
        stop_scheduler()
        console.print("[yellow]Scheduler stopped.[/]")
    elif action == "status":
        status = get_job_status()
        for k, v in status.items():
            console.print(f"  {k}: {v}")
    elif action == "trigger":
        trigger_scan_now()
        console.print("[green]✓ Scan triggered.[/]")
    else:
        console.print(f"[red]Unknown action: {action!r}. Available: start | stop | status | trigger[/]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
