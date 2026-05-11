"""Pydantic schemas for broker and user-profile YAML config files."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ── Broker config schema ──────────────────────────────────────────────────────

class OptOutConfig(BaseModel):
    """Opt-out method descriptor for a broker."""

    url: str
    method: str = "manual"  # manual | form | email | api
    email_address: Optional[str] = None
    notes: Optional[str] = None
    requires_email_verification: bool = False
    requires_manual_captcha: bool = False
    automated_allowed: bool = False  # Must be explicitly true in broker config


class BrokerConfig(BaseModel):
    """Schema for a single broker entry in brokers.yaml."""

    name: str
    slug: str
    category: str
    base_url: str
    search_url_template: Optional[str] = None
    opt_out: OptOutConfig
    required_fields: list[str] = Field(default_factory=list)
    automated_search_allowed: bool = False
    manual_review_required: bool = True
    enabled: bool = True
    notes: Optional[str] = None


class BrokersFile(BaseModel):
    """Top-level structure of brokers.yaml."""

    version: str = "1.0"
    brokers: list[BrokerConfig] = Field(default_factory=list)


# ── User profile schema ───────────────────────────────────────────────────────

class AliasConfig(BaseModel):
    """A name variation or former name the user wants to track."""

    value: str
    kind: str = "name"  # name | email | phone | username


class UserProfileConfig(BaseModel):
    """Schema for profile.yaml — user-owned personal information only."""

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    date_of_birth: Optional[str] = None  # ISO 8601 YYYY-MM-DD
    aliases: list[AliasConfig] = Field(default_factory=list)

    @field_validator("date_of_birth")
    @classmethod
    def _validate_dob(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("date_of_birth must be YYYY-MM-DD")
        return v
