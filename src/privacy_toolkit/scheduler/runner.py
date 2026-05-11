"""APScheduler lifecycle management."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from privacy_toolkit.core.constants import (
    DEFAULT_SCHEDULER_INTERVAL_DAYS,
    SCHEDULER_JOB_ID_RECURRING_SCAN,
)
from privacy_toolkit.core.exceptions import SchedulerError
from privacy_toolkit.core.logging import get_logger
from privacy_toolkit.scheduler.jobs import run_scheduled_scan

logger = get_logger(__name__)

_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    """Return the singleton BackgroundScheduler (lazy-init)."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="UTC")
    return _scheduler


def start_scheduler(interval_days: Optional[int] = None) -> None:
    """Start the background scheduler with the recurring scan job.

    Args:
        interval_days: Override the configured scan interval.
    """
    from privacy_toolkit.config.settings import get_settings
    settings = get_settings()
    days = interval_days or settings.scheduler_interval_days or DEFAULT_SCHEDULER_INTERVAL_DAYS

    scheduler = get_scheduler()
    if scheduler.running:
        logger.info("Scheduler already running.")
        return

    scheduler.add_job(
        run_scheduled_scan,
        trigger=IntervalTrigger(days=days),
        id=SCHEDULER_JOB_ID_RECURRING_SCAN,
        name="Recurring Privacy Scan",
        replace_existing=True,
        next_run_time=datetime.utcnow() + timedelta(days=days),
    )
    scheduler.start()
    logger.info("Scheduler started — next scan in %d day(s).", days)


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
    _scheduler = None


def trigger_scan_now() -> None:
    """Manually trigger the recurring scan job immediately."""
    scheduler = get_scheduler()
    if not scheduler.running:
        raise SchedulerError("Scheduler is not running. Call start_scheduler() first.")
    job = scheduler.get_job(SCHEDULER_JOB_ID_RECURRING_SCAN)
    if job is None:
        raise SchedulerError(f"Job {SCHEDULER_JOB_ID_RECURRING_SCAN!r} not found.")
    job.modify(next_run_time=datetime.utcnow())
    logger.info("Recurring scan job triggered immediately.")


def get_job_status() -> dict[str, object]:
    """Return a status dict for the recurring scan job."""
    scheduler = get_scheduler()
    job = scheduler.get_job(SCHEDULER_JOB_ID_RECURRING_SCAN)
    return {
        "scheduler_running": scheduler.running,
        "job_id": SCHEDULER_JOB_ID_RECURRING_SCAN,
        "next_run": job.next_run_time.isoformat() if job and job.next_run_time else None,
        "enabled": job is not None,
    }
