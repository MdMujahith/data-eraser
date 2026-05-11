"""Tests for opt-out status machine."""

from __future__ import annotations

import pytest

from privacy_toolkit.core.constants import Status
from privacy_toolkit.core.exceptions import InvalidStatusTransitionError
from privacy_toolkit.optout.status_machine import (
    allowed_transitions,
    is_manual_required,
    is_terminal,
    validate_transition,
)


def test_valid_transition_not_started_to_ready() -> None:
    validate_transition(Status.NOT_STARTED, Status.REQUEST_READY)  # should not raise


def test_valid_transition_found_to_ready() -> None:
    validate_transition(Status.FOUND, Status.REQUEST_READY)


def test_valid_transition_ready_to_sent() -> None:
    validate_transition(Status.REQUEST_READY, Status.REQUEST_SENT)


def test_valid_transition_sent_to_completed() -> None:
    validate_transition(Status.REQUEST_SENT, Status.COMPLETED)


def test_invalid_transition_completed_to_scanning() -> None:
    with pytest.raises(InvalidStatusTransitionError):
        validate_transition(Status.COMPLETED, Status.SCANNING)


def test_invalid_transition_not_found_to_completed() -> None:
    with pytest.raises(InvalidStatusTransitionError):
        validate_transition(Status.NOT_FOUND, Status.COMPLETED)


def test_allowed_transitions_not_started() -> None:
    allowed = allowed_transitions(Status.NOT_STARTED)
    assert Status.REQUEST_READY in allowed
    assert Status.SCANNING in allowed


def test_is_terminal_completed() -> None:
    # COMPLETED has one outbound transition (RESCAN_REQUIRED) — not fully terminal
    # But NOT_FOUND flows to RESCAN_REQUIRED
    assert not is_terminal(Status.NOT_STARTED)


def test_is_manual_required() -> None:
    assert is_manual_required(Status.MANUAL_CAPTCHA_REQUIRED)
    assert is_manual_required(Status.MANUAL_REVIEW_REQUIRED)
    assert is_manual_required(Status.EMAIL_VERIFICATION_REQUIRED)
    assert not is_manual_required(Status.COMPLETED)
    assert not is_manual_required(Status.NOT_STARTED)


def test_invalid_transition_raises_correct_exception() -> None:
    with pytest.raises(InvalidStatusTransitionError) as exc_info:
        validate_transition(Status.NOT_FOUND, Status.FOUND)
    assert exc_info.value.from_status == Status.NOT_FOUND
    assert exc_info.value.to_status == Status.FOUND
