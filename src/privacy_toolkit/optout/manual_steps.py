"""Generate human-readable manual opt-out checklists."""

from __future__ import annotations

from privacy_toolkit.db.models import Broker

_REASON_PREAMBLES: dict[str, str] = {
    "captcha": "A CAPTCHA was detected. You must complete this opt-out manually:",
    "auto_disabled": "Automated opt-out is disabled. Follow these steps manually:",
    "broker_policy": "This broker requires manual opt-out per its policy:",
    "default": "Manual action required for this opt-out:",
}


def build_manual_checklist(broker: Broker, reason: str = "default") -> list[str]:
    """Return a step-by-step checklist for a manual opt-out.

    Args:
        broker: The :class:`~privacy_toolkit.db.models.Broker` to opt out of.
        reason: One of ``captcha``, ``auto_disabled``, ``broker_policy``, ``default``.

    Returns:
        Ordered list of instruction strings.
    """
    preamble = _REASON_PREAMBLES.get(reason, _REASON_PREAMBLES["default"])
    steps: list[str] = [preamble]

    if broker.opt_out_method == "email" and broker.opt_out_email:
        steps += [
            f"1. Compose an email to: {broker.opt_out_email}",
            "2. Subject: Data Removal Request",
            "3. Body: Request removal of your personal data, including full name, address, and phone.",
            "4. Send and save a copy of the sent email as evidence.",
            "5. Mark this request as COMPLETED once you receive confirmation.",
        ]
    else:
        opt_url = broker.opt_out_url or broker.base_url
        steps += [
            f"1. Open the opt-out page: {opt_url}",
            "2. Fill in your personal information as required.",
            "3. Complete any CAPTCHA challenge if present.",
            "4. Submit the form and save a screenshot as evidence.",
        ]
        if broker.requires_email_verification:
            steps.append("5. Check your email inbox and click the verification link.")
            steps.append("6. Mark this request as COMPLETED after email confirmation.")
        else:
            steps.append("5. Mark this request as COMPLETED once you receive a confirmation page or email.")

    if broker.opt_out_notes:
        steps.append(f"Note: {broker.opt_out_notes}")

    return steps
