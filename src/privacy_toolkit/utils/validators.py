"""Input validation helpers."""

from __future__ import annotations

import re
from typing import Optional


_EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$", re.IGNORECASE)
_PHONE_RE = re.compile(r"^\+?[\d\s\-().]{7,15}$")
_ZIP_RE   = re.compile(r"^\d{5}(-\d{4})?$")
_DATE_RE  = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_valid_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value.strip()))


def is_valid_phone(value: str) -> bool:
    return bool(_PHONE_RE.match(value.strip()))


def is_valid_zip(value: str) -> bool:
    return bool(_ZIP_RE.match(value.strip()))


def is_valid_date(value: str) -> bool:
    """Validate YYYY-MM-DD format."""
    return bool(_DATE_RE.match(value.strip()))


def validate_profile_field(field: str, value: Optional[str]) -> Optional[str]:
    """Return an error string or None if valid.

    Args:
        field: Field name (email, phone, zip_code, date_of_birth).
        value: The value to validate.
    """
    if value is None or value.strip() == "":
        return None  # Optional fields are allowed to be blank
    checks: dict[str, tuple] = {
        "email":         (is_valid_email, "Invalid email format"),
        "phone":         (is_valid_phone, "Invalid phone format"),
        "zip_code":      (is_valid_zip,   "Invalid ZIP code"),
        "date_of_birth": (is_valid_date,  "Invalid date — use YYYY-MM-DD"),
    }
    if field in checks:
        fn, msg = checks[field]
        if not fn(value):
            return msg
    return None
