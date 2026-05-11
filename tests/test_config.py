"""Tests for config/settings."""

from __future__ import annotations

import os

import pytest

from privacy_toolkit.config.settings import Settings, reset_settings


def test_default_settings() -> None:
    s = Settings()
    assert s.log_level == "INFO"
    assert s.proxy_mode == "none"
    assert s.auto_optout_enabled is False
    assert s.privacy_verify_enabled is False
    assert s.request_retry_max == 3


def test_log_level_normalised() -> None:
    s = Settings(log_level="debug")
    assert s.log_level == "DEBUG"


def test_invalid_proxy_mode() -> None:
    with pytest.raises(Exception):
        Settings(proxy_mode="invalid_mode")


def test_effective_proxy_url_tor() -> None:
    s = Settings(proxy_mode="tor", tor_socks_host="127.0.0.1", tor_socks_port=9050)
    assert s.effective_proxy_url == "socks5://127.0.0.1:9050"


def test_effective_proxy_url_none() -> None:
    s = Settings(proxy_mode="none")
    assert s.effective_proxy_url is None


def test_reset_settings() -> None:
    reset_settings()
    # Should not raise
    from privacy_toolkit.config.settings import get_settings
    s = get_settings()
    assert s is not None
    reset_settings()
