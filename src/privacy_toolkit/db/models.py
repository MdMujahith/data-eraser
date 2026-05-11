"""SQLAlchemy ORM models for the Privacy Toolkit local database."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared declarative base."""


# ── UserProfile ───────────────────────────────────────────────────────────────

class UserProfile(Base):
    """Encrypted storage of the user's personal identifiers."""

    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(100), unique=True, default="default")

    # All sensitive fields stored encrypted (Fernet tokens as text)
    full_name_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_of_birth_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    aliases: Mapped[list[Alias]] = relationship(
        "Alias", back_populates="profile", cascade="all, delete-orphan"
    )
    scan_runs: Mapped[list[ScanRun]] = relationship("ScanRun", back_populates="profile")

    def __repr__(self) -> str:
        return f"<UserProfile id={self.id} label={self.label!r}>"


# ── Alias ─────────────────────────────────────────────────────────────────────

class Alias(Base):
    """Name variations, former names, or other identifier aliases."""

    __tablename__ = "aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), nullable=False)
    value_enc: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String(50), default="name")  # name|email|phone|username
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    profile: Mapped[UserProfile] = relationship("UserProfile", back_populates="aliases")

    def __repr__(self) -> str:
        return f"<Alias id={self.id} kind={self.kind!r}>"


# ── Broker ────────────────────────────────────────────────────────────────────

class Broker(Base):
    """Registry of known data brokers."""

    __tablename__ = "brokers"
    __table_args__ = (UniqueConstraint("slug", name="uq_broker_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    search_url_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    opt_out_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    opt_out_method: Mapped[str] = mapped_column(String(50), default="manual")
    opt_out_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    opt_out_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requires_email_verification: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_manual_captcha: Mapped[bool] = mapped_column(Boolean, default=False)
    automated_search_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    automated_optout_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    manual_review_required: Mapped[bool] = mapped_column(Boolean, default=True)
    required_fields: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    findings: Mapped[list[BrokerFinding]] = relationship(
        "BrokerFinding", back_populates="broker", cascade="all, delete-orphan"
    )
    optout_requests: Mapped[list[OptOutRequest]] = relationship(
        "OptOutRequest", back_populates="broker"
    )

    def __repr__(self) -> str:
        return f"<Broker slug={self.slug!r} category={self.category!r}>"


# ── BrokerFinding ─────────────────────────────────────────────────────────────

class BrokerFinding(Base):
    """A record discovered during a scan on a given broker."""

    __tablename__ = "broker_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    broker_id: Mapped[int] = mapped_column(ForeignKey("brokers.id"), nullable=False)
    scan_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scan_runs.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="FOUND")
    result_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # non-sensitive preview
    raw_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA-256 of raw HTML
    found_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    broker: Mapped[Broker] = relationship("Broker", back_populates="findings")
    scan_run: Mapped[Optional[ScanRun]] = relationship("ScanRun", back_populates="findings")
    evidence: Mapped[list[Evidence]] = relationship(
        "Evidence", back_populates="finding", cascade="all, delete-orphan"
    )
    optout_requests: Mapped[list[OptOutRequest]] = relationship(
        "OptOutRequest", back_populates="finding"
    )

    def __repr__(self) -> str:
        return f"<BrokerFinding id={self.id} status={self.status!r}>"


# ── OptOutRequest ─────────────────────────────────────────────────────────────

class OptOutRequest(Base):
    """Tracks a single opt-out request lifecycle for a broker finding."""

    __tablename__ = "optout_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    broker_id: Mapped[int] = mapped_column(ForeignKey("brokers.id"), nullable=False)
    finding_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("broker_findings.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="NOT_STARTED")
    method: Mapped[str] = mapped_column(String(50), default="manual")
    submission_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confirmation_code: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    email_verification_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    broker: Mapped[Broker] = relationship("Broker", back_populates="optout_requests")
    finding: Mapped[Optional[BrokerFinding]] = relationship(
        "BrokerFinding", back_populates="optout_requests"
    )
    evidence: Mapped[list[Evidence]] = relationship(
        "Evidence", back_populates="optout_request", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<OptOutRequest id={self.id} status={self.status!r}>"


# ── Evidence ──────────────────────────────────────────────────────────────────

class Evidence(Base):
    """Stores screenshot paths, HTML snapshots, or confirmation receipts."""

    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    finding_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("broker_findings.id"), nullable=True
    )
    optout_request_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("optout_requests.id"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(50), default="html_snapshot")
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    finding: Mapped[Optional[BrokerFinding]] = relationship(
        "BrokerFinding", back_populates="evidence"
    )
    optout_request: Mapped[Optional[OptOutRequest]] = relationship(
        "OptOutRequest", back_populates="evidence"
    )

    def __repr__(self) -> str:
        return f"<Evidence id={self.id} kind={self.kind!r}>"


# ── ScanRun ───────────────────────────────────────────────────────────────────

class ScanRun(Base):
    """Records a complete scan execution across brokers."""

    __tablename__ = "scan_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user_profiles.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="NOT_STARTED")
    brokers_scanned: Mapped[int] = mapped_column(Integer, default=0)
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    proxy_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(50), default="manual")  # manual|scheduler
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    profile: Mapped[Optional[UserProfile]] = relationship(
        "UserProfile", back_populates="scan_runs"
    )
    findings: Mapped[list[BrokerFinding]] = relationship(
        "BrokerFinding", back_populates="scan_run"
    )

    def __repr__(self) -> str:
        return f"<ScanRun id={self.id} status={self.status!r}>"


# ── AppEvent ──────────────────────────────────────────────────────────────────

class AppEvent(Base):
    """Immutable audit log for significant application events."""

    __tablename__ = "app_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info")
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<AppEvent type={self.event_type!r} severity={self.severity!r}>"
