"""Tests for database setup and repository layer."""

from __future__ import annotations

import pytest

from privacy_toolkit.db.database import get_db, health_check, reset_db
from privacy_toolkit.db.repository import (
    BrokerRepository,
    ScanRunRepository,
    UserProfileRepository,
)


@pytest.fixture(autouse=True)
def fresh_db():
    reset_db("sqlite:///:memory:")
    yield
    reset_db("sqlite:///:memory:")


def test_health_check() -> None:
    assert health_check() is True


def test_create_profile() -> None:
    with get_db() as db:
        repo = UserProfileRepository(db)
        p = repo.create(label="test", city="Austin", state="TX")
        assert p.id is not None
        assert p.label == "test"


def test_get_or_create_profile() -> None:
    with get_db() as db:
        repo = UserProfileRepository(db)
        p1 = repo.get_or_create("default")
        p2 = repo.get_or_create("default")
        assert p1.id == p2.id


def test_create_broker() -> None:
    with get_db() as db:
        repo = BrokerRepository(db)
        b = repo.create(
            name="TestBroker",
            slug="test-broker",
            category="people_search",
            base_url="https://example.invalid",
        )
        assert b.id is not None
        assert b.slug == "test-broker"


def test_broker_upsert() -> None:
    with get_db() as db:
        repo = BrokerRepository(db)
        b1 = repo.upsert("slug-x", name="Broker X", category="other", base_url="https://x.invalid")
        b2 = repo.upsert("slug-x", name="Broker X Updated", category="other", base_url="https://x.invalid")
        assert b1.id == b2.id
        assert b2.name == "Broker X Updated"


def test_broker_count() -> None:
    with get_db() as db:
        repo = BrokerRepository(db)
        assert repo.count() == 0
        repo.create(name="A", slug="a", category="other", base_url="https://a.invalid")
        assert repo.count() == 1


def test_scan_run_create_and_update() -> None:
    with get_db() as db:
        repo = ScanRunRepository(db)
        run = repo.create(status="NOT_STARTED", triggered_by="manual")
        assert run.id is not None
        updated = repo.update(run.id, status="COMPLETED", brokers_scanned=5)
        assert updated.status == "COMPLETED"
        assert updated.brokers_scanned == 5
