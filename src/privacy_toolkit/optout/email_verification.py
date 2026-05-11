"""Email verification tracking helpers."""

from __future__ import annotations

from privacy_toolkit.core.constants import Status
from privacy_toolkit.core.logging import get_logger
from privacy_toolkit.db.database import get_db
from privacy_toolkit.db.repository import AppEventRepository, OptOutRequestRepository

logger = get_logger(__name__)


def mark_email_verified(request_id: int) -> None:
    """Advance an opt-out request from EMAIL_VERIFICATION_REQUIRED → COMPLETED.

    Args:
        request_id: The :class:`~privacy_toolkit.db.models.OptOutRequest` ID.
    """
    from privacy_toolkit.optout.status_machine import validate_transition

    with get_db() as db:
        repo = OptOutRequestRepository(db)
        event_repo = AppEventRepository(db)

        req = repo.get(request_id)
        validate_transition(req.status, Status.COMPLETED)
        repo.update_status(
            request_id,
            Status.COMPLETED,
            notes="Email verification confirmed by user.",
        )
        event_repo.log(
            "email_verified",
            f"Request #{request_id} email verification confirmed.",
            severity="info",
        )
        logger.info("Request #%d marked as email-verified and COMPLETED.", request_id)
