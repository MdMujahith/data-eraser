"""Redaction helpers — mask sensitive values for logs and UI display."""

from __future__ import annotations

import re
from typing import Any


def redact_email(email: str) -> str:
    """Mask email: ``john@example.com`` → ``j***@example.com``."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        return f"{local}***@{domain}"
    return f"{local[0]}***@{domain}"


def redact_phone(phone: str) -> str:
    """Mask phone: ``9876543210`` → ``98******10``."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 4:
        return "***"
    return f"{digits[:2]}{'*' * (len(digits) - 4)}{digits[-2:]}"


def redact_name(name: str) -> str:
    """Mask full name: ``John Doe`` → ``J*** D***``."""
    parts = name.strip().split()
    return " ".join(f"{p[0]}***" if p else "***" for p in parts)


def redact_address(address: str) -> str:
    """Mask street address: keep first word, mask rest."""
    parts = address.strip().split()
    if not parts:
        return "***"
    return f"{parts[0]} ***"


def redact_dob(dob: str) -> str:
    """Mask date of birth: ``1990-05-23`` → ``****-05-**``."""
    if re.match(r"^\d{4}-\d{2}-\d{2}$", dob):
        return f"****-{dob[5:7]}-**"
    return "***"


def redact_value(field_name: str, value: str) -> str:
    """Dispatch to the correct redactor by field name.

    Args:
        field_name: Canonical field name (e.g. ``"email"``, ``"phone"``).
        value: Plaintext value to redact.

    Returns:
        Redacted string safe for logs and UI.
    """
    dispatch: dict[str, Any] = {
        "email": redact_email,
        "phone": redact_phone,
        "full_name": redact_name,
        "address": redact_address,
        "date_of_birth": redact_dob,
    }
    fn = dispatch.get(field_name.lower())
    if fn:
        return fn(value)
    # Generic fallback: show first char + asterisks
    return f"{value[0]}{'*' * (len(value) - 1)}" if value else "***"


def redact_dict(data: dict[str, Any], sensitive_keys: list[str]) -> dict[str, Any]:
    """Return a copy of *data* with sensitive keys redacted.

    Args:
        data: Source dictionary.
        sensitive_keys: Keys whose values should be masked.

    Returns:
        New dict with sensitive values replaced by redacted strings.
    """
    result = dict(data)
    for key in sensitive_keys:
        if key in result and result[key] is not None:
            result[key] = redact_value(key, str(result[key]))
    return result
