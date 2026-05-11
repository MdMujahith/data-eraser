"""Evidence capture helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from platformdirs import user_data_dir

from privacy_toolkit.core.constants import APP_SLUG
from privacy_toolkit.core.logging import get_logger

logger = get_logger(__name__)


def _evidence_dir() -> Path:
    d = Path(user_data_dir(APP_SLUG, appauthor=False)) / "evidence"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_html_evidence(
    broker_slug: str,
    html_content: str,
    finding_id: Optional[int] = None,
) -> tuple[Path, str]:
    """Write an HTML snapshot to the evidence directory.

    Returns:
        ``(file_path, sha256_hash)``
    """
    content_hash = hashlib.sha256(html_content.encode()).hexdigest()
    filename = f"{broker_slug}_{finding_id or 'unknown'}_{content_hash[:12]}.html"
    path = _evidence_dir() / filename
    path.write_text(html_content, encoding="utf-8")
    logger.debug("Evidence saved: %s", path)
    return path, content_hash
