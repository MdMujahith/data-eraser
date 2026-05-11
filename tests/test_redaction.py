"""Tests for security/redaction."""

from __future__ import annotations

import pytest

from privacy_toolkit.security.redaction import (
    redact_dict,
    redact_dob,
    redact_email,
    redact_name,
    redact_phone,
    redact_value,
)


def test_redact_email_standard() -> None:
    assert redact_email("john@example.com") == "j***@example.com"


def test_redact_email_short_local() -> None:
    result = redact_email("a@b.com")
    assert "@" in result
    assert "***" in result


def test_redact_email_no_at() -> None:
    assert redact_email("notanemail") == "***"


def test_redact_phone_10digit() -> None:
    result = redact_phone("9876543210")
    assert result.startswith("98")
    assert result.endswith("10")
    assert "****" in result


def test_redact_phone_formatted() -> None:
    result = redact_phone("987-654-3210")
    assert "****" in result


def test_redact_name() -> None:
    result = redact_name("John Doe")
    assert result == "J*** D***"


def test_redact_name_single() -> None:
    result = redact_name("Madonna")
    assert result == "M***"


def test_redact_dob() -> None:
    result = redact_dob("1990-05-23")
    assert result == "****-05-**"


def test_redact_dob_invalid() -> None:
    assert redact_dob("not-a-date") == "***"


def test_redact_value_dispatch() -> None:
    assert "***" in redact_value("email", "test@test.com")
    assert "***" in redact_value("phone", "1234567890")
    assert "***" in redact_value("full_name", "Jane Smith")


def test_redact_dict() -> None:
    data = {"email": "bob@example.com", "city": "Austin", "phone": "5551234567"}
    result = redact_dict(data, sensitive_keys=["email", "phone"])
    assert "***" in result["email"]
    assert "***" in result["phone"]
    assert result["city"] == "Austin"  # non-sensitive unchanged


def test_redact_dict_missing_key() -> None:
    data = {"city": "Austin"}
    result = redact_dict(data, sensitive_keys=["email"])
    assert result == {"city": "Austin"}  # no KeyError
