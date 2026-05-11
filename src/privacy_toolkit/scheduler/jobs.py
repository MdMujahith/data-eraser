"""APScheduler job definitions for recurring scans."""

from __future__ import annotations

from datetime import datetime

from privacy_toolkit.core.constants import SCHEDULER_JOB_ID_RECURRING_SCAN
from privacy_toolkit.core.logging import get_logger

logger = get_logger(__name__)


def run_scheduled_scan() -> None:
    """Job function executed by APScheduler for recurring scans."""
    from privacy_toolkit.recon.scanner import Scanner

    logger.info("[Scheduler] Starting recurring privacy scan at %s", datetime.utcnow().isoformat())
    scanner = Scanner(triggered_by="scheduler")
    summary = scanner.run()
    if summary.get("aborted"):
        logger.error("[Scheduler] Scan aborted: %s", summary.get("error"))
    else:
        logger.info(
            "[Scheduler] Scan complete — %d findings in %d brokers.",
            summary.get("findings", 0),
            summary.get("brokers_scanned", 0),
        )
