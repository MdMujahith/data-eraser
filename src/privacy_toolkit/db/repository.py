"""Repository layer — all DB access goes through these classes.

No raw SQL or ORM queries outside this module.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from privacy_toolkit.core.constants import Status
from privacy_toolkit.core.exceptions import RecordNotFoundError
from privacy_toolkit.db.models import (
    Alias,
    AppEvent,
    Broker,
    BrokerFinding,
    Evidence,
    OptOutRequest,
    ScanRun,
    UserProfile,
)


# ── UserProfile ───────────────────────────────────────────────────────────────

class UserProfileRepository:
    """CRUD for :class:`~privacy_toolkit.db.models.UserProfile`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, label: str = "default", **kwargs: str | None) -> UserProfile:
        profile = UserProfile(label=label, **kwargs)
        self.db.add(profile)
        self.db.flush()
        return profile

    def get(self, profile_id: int) -> UserProfile:
        obj = self.db.get(UserProfile, profile_id)
        if obj is None:
            raise RecordNotFoundError("UserProfile", profile_id)
        return obj

    def get_by_label(self, label: str = "default") -> Optional[UserProfile]:
        stmt = select(UserProfile).where(UserProfile.label == label)
        return self.db.execute(stmt).scalars().first()

    def get_or_create(self, label: str = "default") -> UserProfile:
        existing = self.get_by_label(label)
        if existing:
            return existing
        return self.create(label=label)

    def update(self, profile_id: int, **kwargs: str | None) -> UserProfile:
        profile = self.get(profile_id)
        for k, v in kwargs.items():
            setattr(profile, k, v)
        self.db.flush()
        return profile

    def list_all(self) -> Sequence[UserProfile]:
        return self.db.execute(select(UserProfile)).scalars().all()


# ── Broker ────────────────────────────────────────────────────────────────────

class BrokerRepository:
    """CRUD for :class:`~privacy_toolkit.db.models.Broker`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **kwargs: object) -> Broker:
        broker = Broker(**kwargs)
        self.db.add(broker)
        self.db.flush()
        return broker

    def get(self, broker_id: int) -> Broker:
        obj = self.db.get(Broker, broker_id)
        if obj is None:
            raise RecordNotFoundError("Broker", broker_id)
        return obj

    def get_by_slug(self, slug: str) -> Optional[Broker]:
        stmt = select(Broker).where(Broker.slug == slug)
        return self.db.execute(stmt).scalars().first()

    def list_enabled(self) -> Sequence[Broker]:
        stmt = select(Broker).where(Broker.enabled == True).order_by(Broker.name)  # noqa: E712
        return self.db.execute(stmt).scalars().all()

    def list_by_category(self, category: str) -> Sequence[Broker]:
        stmt = (
            select(Broker)
            .where(Broker.enabled == True, Broker.category == category)  # noqa: E712
            .order_by(Broker.name)
        )
        return self.db.execute(stmt).scalars().all()

    def count(self) -> int:
        return len(self.db.execute(select(Broker)).scalars().all())

    def categories(self) -> list[str]:
        rows = self.db.execute(select(Broker.category).distinct()).scalars().all()
        return sorted(rows)

    def upsert(self, slug: str, **kwargs: object) -> Broker:
        existing = self.get_by_slug(slug)
        if existing:
            for k, v in kwargs.items():
                setattr(existing, k, v)
            self.db.flush()
            return existing
        return self.create(slug=slug, **kwargs)


# ── BrokerFinding ─────────────────────────────────────────────────────────────

class BrokerFindingRepository:
    """CRUD for :class:`~privacy_toolkit.db.models.BrokerFinding`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, broker_id: int, scan_run_id: Optional[int] = None, **kwargs: object) -> BrokerFinding:
        finding = BrokerFinding(broker_id=broker_id, scan_run_id=scan_run_id, **kwargs)
        self.db.add(finding)
        self.db.flush()
        return finding

    def get(self, finding_id: int) -> BrokerFinding:
        obj = self.db.get(BrokerFinding, finding_id)
        if obj is None:
            raise RecordNotFoundError("BrokerFinding", finding_id)
        return obj

    def list_by_status(self, status: str) -> Sequence[BrokerFinding]:
        stmt = select(BrokerFinding).where(BrokerFinding.status == status)
        return self.db.execute(stmt).scalars().all()

    def list_by_broker(self, broker_id: int) -> Sequence[BrokerFinding]:
        stmt = (
            select(BrokerFinding)
            .where(BrokerFinding.broker_id == broker_id)
            .order_by(BrokerFinding.found_at.desc())
        )
        return self.db.execute(stmt).scalars().all()

    def count_by_status(self, status: str) -> int:
        return len(self.db.execute(
            select(BrokerFinding).where(BrokerFinding.status == status)
        ).scalars().all())

    def update_status(self, finding_id: int, status: str) -> BrokerFinding:
        finding = self.get(finding_id)
        finding.status = status
        self.db.flush()
        return finding


# ── OptOutRequest ─────────────────────────────────────────────────────────────

class OptOutRequestRepository:
    """CRUD for :class:`~privacy_toolkit.db.models.OptOutRequest`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, broker_id: int, finding_id: Optional[int] = None, **kwargs: object) -> OptOutRequest:
        req = OptOutRequest(broker_id=broker_id, finding_id=finding_id, **kwargs)
        self.db.add(req)
        self.db.flush()
        return req

    def get(self, request_id: int) -> OptOutRequest:
        obj = self.db.get(OptOutRequest, request_id)
        if obj is None:
            raise RecordNotFoundError("OptOutRequest", request_id)
        return obj

    def list_active(self) -> Sequence[OptOutRequest]:
        terminal = [Status.COMPLETED, Status.NOT_FOUND]
        stmt = select(OptOutRequest).where(OptOutRequest.status.notin_(terminal))
        return self.db.execute(stmt).scalars().all()

    def list_by_status(self, status: str) -> Sequence[OptOutRequest]:
        stmt = select(OptOutRequest).where(OptOutRequest.status == status)
        return self.db.execute(stmt).scalars().all()

    def update_status(self, request_id: int, status: str, notes: Optional[str] = None) -> OptOutRequest:
        req = self.get(request_id)
        req.status = status
        if notes:
            req.notes = notes
        if status == Status.COMPLETED:
            req.completed_at = datetime.utcnow()
        self.db.flush()
        return req

    def count_by_status(self, status: str) -> int:
        return len(self.list_by_status(status))

    def count_manual_review(self) -> int:
        manual = [
            Status.MANUAL_CAPTCHA_REQUIRED,
            Status.MANUAL_REVIEW_REQUIRED,
            Status.EMAIL_VERIFICATION_REQUIRED,
        ]
        rows = self.db.execute(
            select(OptOutRequest).where(OptOutRequest.status.in_(manual))
        ).scalars().all()
        return len(rows)


# ── ScanRun ───────────────────────────────────────────────────────────────────

class ScanRunRepository:
    """CRUD for :class:`~privacy_toolkit.db.models.ScanRun`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **kwargs: object) -> ScanRun:
        run = ScanRun(**kwargs)
        self.db.add(run)
        self.db.flush()
        return run

    def get(self, run_id: int) -> ScanRun:
        obj = self.db.get(ScanRun, run_id)
        if obj is None:
            raise RecordNotFoundError("ScanRun", run_id)
        return obj

    def get_latest(self) -> Optional[ScanRun]:
        stmt = select(ScanRun).order_by(ScanRun.created_at.desc()).limit(1)
        return self.db.execute(stmt).scalars().first()

    def update(self, run_id: int, **kwargs: object) -> ScanRun:
        run = self.get(run_id)
        for k, v in kwargs.items():
            setattr(run, k, v)
        self.db.flush()
        return run

    def list_recent(self, limit: int = 10) -> Sequence[ScanRun]:
        stmt = select(ScanRun).order_by(ScanRun.created_at.desc()).limit(limit)
        return self.db.execute(stmt).scalars().all()


# ── Evidence ──────────────────────────────────────────────────────────────────

class EvidenceRepository:
    """CRUD for :class:`~privacy_toolkit.db.models.Evidence`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **kwargs: object) -> Evidence:
        ev = Evidence(**kwargs)
        self.db.add(ev)
        self.db.flush()
        return ev

    def list_for_finding(self, finding_id: int) -> Sequence[Evidence]:
        stmt = select(Evidence).where(Evidence.finding_id == finding_id)
        return self.db.execute(stmt).scalars().all()

    def list_for_optout(self, request_id: int) -> Sequence[Evidence]:
        stmt = select(Evidence).where(Evidence.optout_request_id == request_id)
        return self.db.execute(stmt).scalars().all()


# ── AppEvent ──────────────────────────────────────────────────────────────────

class AppEventRepository:
    """Append-only audit log."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def log(
        self,
        event_type: str,
        message: str,
        severity: str = "info",
        metadata: Optional[dict[str, object]] = None,
    ) -> AppEvent:
        ev = AppEvent(
            event_type=event_type,
            message=message,
            severity=severity,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        self.db.add(ev)
        self.db.flush()
        return ev

    def list_recent(self, limit: int = 50) -> Sequence[AppEvent]:
        stmt = select(AppEvent).order_by(AppEvent.created_at.desc()).limit(limit)
        return self.db.execute(stmt).scalars().all()
