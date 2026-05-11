"""Build opt-out HTTP payloads from broker config."""

from __future__ import annotations

from privacy_toolkit.db.models import Broker


def build_optout_payload(broker: Broker) -> dict[str, str]:
    """Build a minimal form payload for automated opt-out.

    Returns an empty dict for manual-only brokers.  Real field values
    should be injected by the caller from the (decrypted) user profile.
    """
    if broker.opt_out_method == "email":
        return {}  # Email opt-outs use SMTP, not form POST
    # Generic placeholder — implementers extend this per broker adapter
    return {"action": "opt_out", "broker": broker.slug}
