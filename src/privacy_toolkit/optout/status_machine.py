"""Finite-state machine for opt-out request status transitions."""

from __future__ import annotations

from privacy_toolkit.core.constants import Status
from privacy_toolkit.core.exceptions import InvalidStatusTransitionError

# Allowed transitions: from_status → set of valid to_statuses
_TRANSITIONS: dict[str, set[str]] = {
    Status.NOT_STARTED: {Status.REQUEST_READY, Status.SCANNING, Status.FAILED},
    Status.SCANNING: {Status.FOUND, Status.NOT_FOUND, Status.FAILED},
    Status.FOUND: {Status.REQUEST_READY, Status.MANUAL_REVIEW_REQUIRED, Status.FAILED},
    Status.NOT_FOUND: {Status.RESCAN_REQUIRED},
    Status.REQUEST_READY: {
        Status.REQUEST_SENT,
        Status.MANUAL_CAPTCHA_REQUIRED,
        Status.MANUAL_REVIEW_REQUIRED,
        Status.EMAIL_VERIFICATION_REQUIRED,
        Status.FAILED,
    },
    Status.REQUEST_SENT: {
        Status.EMAIL_VERIFICATION_REQUIRED,
        Status.MANUAL_REVIEW_REQUIRED,
        Status.COMPLETED,
        Status.FAILED,
        Status.RESCAN_REQUIRED,
    },
    Status.EMAIL_VERIFICATION_REQUIRED: {
        Status.REQUEST_SENT,
        Status.COMPLETED,
        Status.FAILED,
    },
    Status.MANUAL_CAPTCHA_REQUIRED: {
        Status.REQUEST_SENT,
        Status.MANUAL_REVIEW_REQUIRED,
        Status.FAILED,
    },
    Status.MANUAL_REVIEW_REQUIRED: {
        Status.REQUEST_READY,
        Status.REQUEST_SENT,
        Status.COMPLETED,
        Status.FAILED,
        Status.RESCAN_REQUIRED,
    },
    Status.COMPLETED: {Status.RESCAN_REQUIRED},
    Status.FAILED: {Status.NOT_STARTED, Status.REQUEST_READY, Status.RESCAN_REQUIRED},
    Status.RESCAN_REQUIRED: {Status.SCANNING, Status.NOT_STARTED},
}


def validate_transition(from_status: str, to_status: str) -> None:
    """Raise :class:`InvalidStatusTransitionError` if the transition is illegal.

    Args:
        from_status: Current status string.
        to_status: Desired next status string.
    """
    allowed = _TRANSITIONS.get(from_status, set())
    if to_status not in allowed:
        raise InvalidStatusTransitionError(from_status, to_status)


def allowed_transitions(from_status: str) -> set[str]:
    """Return the set of valid next statuses from *from_status*."""
    return set(_TRANSITIONS.get(from_status, set()))


def is_terminal(status: str) -> bool:
    """Return ``True`` if *status* has no allowed outbound transitions."""
    return not _TRANSITIONS.get(status)


def is_manual_required(status: str) -> bool:
    """Return ``True`` if the status requires human intervention."""
    return status in Status.MANUAL_REQUIRED
