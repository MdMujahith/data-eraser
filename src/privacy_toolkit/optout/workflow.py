"""Opt-out workflow engine.

Automated submission is **disabled by default** and must be explicitly enabled
via ``auto_optout_enabled=true`` in settings.  All automated opt-outs respect
broker-level ``automated_optout_allowed`` flags.

For brokers that require CAPTCHA or manual steps, a checklist is generated
and the request status is set to ``MANUAL_CAPTCHA_REQUIRED`` or
``MANUAL_REVIEW_REQUIRED``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from privacy_toolkit.core.constants import Status
from privacy_toolkit.core.exceptions import AutoOptOutDisabledError, CaptchaRequiredError
from privacy_toolkit.core.logging import get_logger
from privacy_toolkit.db.database import get_db
from privacy_toolkit.db.repository import (
    AppEventRepository,
    BrokerFindingRepository,
    BrokerRepository,
    OptOutRequestRepository,
)
from privacy_toolkit.optout.manual_steps import build_manual_checklist
from privacy_toolkit.optout.request_builder import build_optout_payload
from privacy_toolkit.optout.status_machine import validate_transition
from privacy_toolkit.network.client import NetworkClient

logger = get_logger(__name__)


@dataclass
class WorkflowResult:
    """Outcome of a single opt-out workflow execution."""

    request_id: int
    broker_slug: str
    status: str
    message: str
    manual_steps: Optional[list[str]] = None
    error: Optional[str] = None


class OptOutWorkflow:
    """Drive an opt-out request from FOUND → (COMPLETED | MANUAL_*)."""

    def __init__(self, client: Optional[NetworkClient] = None) -> None:
        from privacy_toolkit.network.client import build_client_from_settings
        self._client = client or build_client_from_settings()

    def initiate(self, finding_id: int) -> WorkflowResult:
        """Create or resume an opt-out request for a given finding.

        Args:
            finding_id: ID of the :class:`~privacy_toolkit.db.models.BrokerFinding`.

        Returns:
            :class:`WorkflowResult` with new status and any manual steps.
        """
        from privacy_toolkit.config.settings import get_settings
        settings = get_settings()

        with get_db() as db:
            finding_repo = BrokerFindingRepository(db)
            broker_repo = BrokerRepository(db)
            optout_repo = OptOutRequestRepository(db)
            event_repo = AppEventRepository(db)

            finding = finding_repo.get(finding_id)
            broker = broker_repo.get(finding.broker_id)

            # Create opt-out request record
            req = optout_repo.create(
                broker_id=broker.id,
                finding_id=finding.id,
                status=Status.NOT_STARTED,
                method=broker.opt_out_method,
                submission_url=broker.opt_out_url,
            )

            # Transition to REQUEST_READY
            validate_transition(Status.NOT_STARTED, Status.REQUEST_READY)
            req = optout_repo.update_status(req.id, Status.REQUEST_READY)

            # CAPTCHA check
            if broker.requires_manual_captcha:
                validate_transition(Status.REQUEST_READY, Status.MANUAL_CAPTCHA_REQUIRED)
                req = optout_repo.update_status(
                    req.id,
                    Status.MANUAL_CAPTCHA_REQUIRED,
                    notes="CAPTCHA detected — manual submission required.",
                )
                steps = build_manual_checklist(broker, reason="captcha")
                event_repo.log("optout_captcha_required", f"Broker: {broker.slug}")
                return WorkflowResult(
                    request_id=req.id,
                    broker_slug=broker.slug,
                    status=Status.MANUAL_CAPTCHA_REQUIRED,
                    message="CAPTCHA required — see manual steps.",
                    manual_steps=steps,
                )

            # Auto opt-out gate
            if not settings.auto_optout_enabled:
                validate_transition(Status.REQUEST_READY, Status.MANUAL_REVIEW_REQUIRED)
                req = optout_repo.update_status(
                    req.id,
                    Status.MANUAL_REVIEW_REQUIRED,
                    notes="Automated opt-out disabled — manual action required.",
                )
                steps = build_manual_checklist(broker, reason="auto_disabled")
                return WorkflowResult(
                    request_id=req.id,
                    broker_slug=broker.slug,
                    status=Status.MANUAL_REVIEW_REQUIRED,
                    message="Automated opt-out is disabled. Complete manually.",
                    manual_steps=steps,
                )

            # Broker-level automation gate
            if not broker.automated_optout_allowed:
                validate_transition(Status.REQUEST_READY, Status.MANUAL_REVIEW_REQUIRED)
                req = optout_repo.update_status(
                    req.id,
                    Status.MANUAL_REVIEW_REQUIRED,
                    notes="Broker does not allow automated opt-out.",
                )
                steps = build_manual_checklist(broker, reason="broker_policy")
                return WorkflowResult(
                    request_id=req.id,
                    broker_slug=broker.slug,
                    status=Status.MANUAL_REVIEW_REQUIRED,
                    message="Broker policy requires manual opt-out.",
                    manual_steps=steps,
                )

            # Automated submission path
            try:
                payload = build_optout_payload(broker)
                resp = self._client.post(broker.opt_out_url or broker.base_url, data=payload)

                validate_transition(Status.REQUEST_READY, Status.REQUEST_SENT)
                req = optout_repo.update_status(req.id, Status.REQUEST_SENT)

                if broker.requires_email_verification:
                    validate_transition(Status.REQUEST_SENT, Status.EMAIL_VERIFICATION_REQUIRED)
                    req = optout_repo.update_status(req.id, Status.EMAIL_VERIFICATION_REQUIRED)
                    event_repo.log("optout_email_verification", f"Broker: {broker.slug}")
                    return WorkflowResult(
                        request_id=req.id,
                        broker_slug=broker.slug,
                        status=Status.EMAIL_VERIFICATION_REQUIRED,
                        message="Check your email to confirm the opt-out request.",
                    )

                validate_transition(Status.REQUEST_SENT, Status.COMPLETED)
                req = optout_repo.update_status(req.id, Status.COMPLETED)
                event_repo.log("optout_completed", f"Broker: {broker.slug}")
                return WorkflowResult(
                    request_id=req.id,
                    broker_slug=broker.slug,
                    status=Status.COMPLETED,
                    message=f"Opt-out submitted successfully (HTTP {resp.status_code}).",
                )

            except Exception as exc:
                validate_transition(Status.REQUEST_READY, Status.FAILED)
                optout_repo.update_status(req.id, Status.FAILED, notes=str(exc))
                logger.error("Opt-out failed for broker %s: %s", broker.slug, exc)
                return WorkflowResult(
                    request_id=req.id,
                    broker_slug=broker.slug,
                    status=Status.FAILED,
                    message="Opt-out submission failed.",
                    error=str(exc),
                )
