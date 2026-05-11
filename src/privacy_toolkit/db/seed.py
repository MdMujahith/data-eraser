"""Seed the database with broker configs from YAML and a demo profile."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from privacy_toolkit.config.loader import load_brokers
from privacy_toolkit.core.logging import get_logger
from privacy_toolkit.db.database import get_db
from privacy_toolkit.db.repository import AppEventRepository, BrokerRepository, UserProfileRepository

logger = get_logger(__name__)

_DEFAULT_BROKERS_PATH = Path(__file__).parent.parent.parent.parent / "data" / "brokers.sample.yaml"


def seed_brokers(brokers_path: Optional[Path] = None, force: bool = False) -> int:
    """Import brokers from YAML into the database.

    Args:
        brokers_path: Path to the brokers YAML file.
        force: Re-upsert even if brokers already exist.

    Returns:
        Number of brokers upserted.
    """
    path = brokers_path or _DEFAULT_BROKERS_PATH
    brokers_file = load_brokers(path)
    count = 0

    with get_db() as db:
        repo = BrokerRepository(db)
        event_repo = AppEventRepository(db)

        for bc in brokers_file.brokers:
            repo.upsert(
                slug=bc.slug,
                name=bc.name,
                category=bc.category,
                base_url=bc.base_url,
                search_url_template=bc.search_url_template,
                opt_out_url=bc.opt_out.url,
                opt_out_method=bc.opt_out.method,
                opt_out_email=bc.opt_out.email_address,
                opt_out_notes=bc.opt_out.notes,
                requires_email_verification=bc.opt_out.requires_email_verification,
                requires_manual_captcha=bc.opt_out.requires_manual_captcha,
                automated_search_allowed=bc.automated_search_allowed,
                automated_optout_allowed=bc.opt_out.automated_allowed,
                manual_review_required=bc.manual_review_required,
                required_fields=json.dumps(bc.required_fields),
                enabled=bc.enabled,
                notes=bc.notes,
            )
            count += 1

        event_repo.log("seed_brokers", f"Seeded {count} brokers from {path}", severity="info")
        logger.info("Seeded %d brokers.", count)

    return count


def seed_demo_profile() -> None:
    """Create a placeholder user profile if none exists (for testing only)."""
    with get_db() as db:
        repo = UserProfileRepository(db)
        profile = repo.get_by_label("default")
        if profile:
            logger.info("Default profile already exists — skipping demo seed.")
            return
        repo.create(label="default", city="Anytown", state="TX", zip_code="00000")
        logger.info("Demo profile created (no sensitive data populated).")
