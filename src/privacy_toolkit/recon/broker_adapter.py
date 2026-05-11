"""Broker adapter protocol and built-in sample adapters.

Each adapter defines how to:
1. Build a search URL for a given profile.
2. Parse the response for possible data presence.
3. Determine whether automated search/opt-out is allowed.

Sample adapters use example/placeholder endpoints — they do NOT target live
broker websites.  Replace ``search_url_template`` in ``brokers.sample.yaml``
with actual URLs before use.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from privacy_toolkit.core.types import FindingDict
from privacy_toolkit.network.client import NetworkClient


# ── Result type ───────────────────────────────────────────────────────────────

@dataclass
class ScanResult:
    """Outcome of a single broker adapter scan."""

    broker_slug: str
    found: bool
    result_url: Optional[str] = None
    snippet: Optional[str] = None          # Safe non-sensitive preview text
    raw_html_hash: Optional[str] = None    # SHA-256 of response body (not the body itself)
    error: Optional[str] = None
    requires_manual_review: bool = False
    extra: dict[str, object] = field(default_factory=dict)


# ── Abstract base ─────────────────────────────────────────────────────────────

class BrokerAdapter(ABC):
    """Abstract base for all broker adapters."""

    #: Unique slug matching ``brokers.yaml``
    slug: str = ""
    #: Human-readable name
    name: str = ""
    #: Broker category
    category: str = ""
    #: Base website URL (for display only)
    base_url: str = ""
    #: URL template; supports ``{first_name}``, ``{last_name}``, ``{city}``, ``{state}``
    search_url_template: Optional[str] = None
    #: Profile fields this adapter needs
    required_fields: list[str] = []
    #: Whether automated fetching is permitted per robots.txt / ToS
    automated_search_allowed: bool = False
    #: Whether a human must confirm results
    manual_review_required: bool = True

    def build_search_url(self, profile_fields: dict[str, str]) -> Optional[str]:
        """Interpolate ``search_url_template`` with *profile_fields*.

        Missing fields are replaced with empty string; returns ``None`` if no
        template is defined.
        """
        if not self.search_url_template:
            return None
        try:
            return self.search_url_template.format_map(
                {k: v or "" for k, v in profile_fields.items()}
            )
        except KeyError:
            return self.search_url_template

    @abstractmethod
    def scan(
        self,
        profile_fields: dict[str, str],
        client: NetworkClient,
    ) -> ScanResult:
        """Execute a search and return a :class:`ScanResult`.

        Implementers MUST:
        - Check ``automated_search_allowed`` before making any request.
        - Only use ``client`` for HTTP access.
        - Never log raw PII.
        """

    @staticmethod
    def _hash_body(body: str) -> str:
        return hashlib.sha256(body.encode()).hexdigest()


# ── Sample adapter 1: PeopleFinderDemo ───────────────────────────────────────

class PeopleFinderDemoAdapter(BrokerAdapter):
    """Demo adapter for a fictional people-search broker.

    Uses ``httpbin.org/anything`` as a safe placeholder endpoint.
    """

    slug = "peoplefinder-demo"
    name = "PeopleFinder (Demo)"
    category = "people_search"
    base_url = "https://example-peoplefinder.invalid"
    search_url_template = "https://httpbin.org/anything?q={last_name}+{first_name}&state={state}"
    required_fields = ["first_name", "last_name"]
    automated_search_allowed = True
    manual_review_required = True

    def scan(self, profile_fields: dict[str, str], client: NetworkClient) -> ScanResult:
        if not self.automated_search_allowed:
            return ScanResult(
                broker_slug=self.slug,
                found=False,
                requires_manual_review=True,
                error="Automated search not allowed — manual review required.",
            )

        url = self.build_search_url(profile_fields)
        if not url:
            return ScanResult(broker_slug=self.slug, found=False, error="No search URL")

        try:
            resp = client.get(url)
            body = resp.text
            body_hash = self._hash_body(body)
            # Demo logic: httpbin echoes params — treat any 200 as "possible match"
            found = resp.status_code == 200
            snippet = "Demo adapter — httpbin echo endpoint (not a real broker)"
            return ScanResult(
                broker_slug=self.slug,
                found=found,
                result_url=url,
                snippet=snippet,
                raw_html_hash=body_hash,
                requires_manual_review=True,
            )
        except Exception as exc:
            return ScanResult(broker_slug=self.slug, found=False, error=str(exc))


# ── Sample adapter 2: DataAggregatorDemo ─────────────────────────────────────

class DataAggregatorDemoAdapter(BrokerAdapter):
    """Demo adapter simulating a data aggregator opt-out workflow."""

    slug = "dataaggregator-demo"
    name = "DataAggregator (Demo)"
    category = "data_aggregator"
    base_url = "https://example-dataagg.invalid"
    search_url_template = None  # No automated search allowed
    required_fields = ["full_name", "email"]
    automated_search_allowed = False
    manual_review_required = True

    def scan(self, profile_fields: dict[str, str], client: NetworkClient) -> ScanResult:
        # Automated search is disabled for this broker
        return ScanResult(
            broker_slug=self.slug,
            found=False,
            requires_manual_review=True,
            error=None,
            extra={"manual_note": "Visit opt-out page manually and submit removal request."},
        )


# ── Sample adapter 3: BackgroundCheckDemo ────────────────────────────────────

class BackgroundCheckDemoAdapter(BrokerAdapter):
    """Demo adapter for a fictional background-check broker."""

    slug = "bgcheck-demo"
    name = "BackgroundCheck (Demo)"
    category = "background_check"
    base_url = "https://example-bgcheck.invalid"
    search_url_template = "https://httpbin.org/get?name={last_name}_{first_name}"
    required_fields = ["first_name", "last_name", "state"]
    automated_search_allowed = True
    manual_review_required = True

    def scan(self, profile_fields: dict[str, str], client: NetworkClient) -> ScanResult:
        if not self.automated_search_allowed:
            return ScanResult(broker_slug=self.slug, found=False, requires_manual_review=True)

        url = self.build_search_url(profile_fields)
        if not url:
            return ScanResult(broker_slug=self.slug, found=False, error="No search URL")

        try:
            resp = client.get(url)
            body_hash = self._hash_body(resp.text)
            found = resp.status_code == 200
            return ScanResult(
                broker_slug=self.slug,
                found=found,
                result_url=url,
                snippet="Demo adapter — httpbin GET echo (not a real broker)",
                raw_html_hash=body_hash,
                requires_manual_review=True,
            )
        except Exception as exc:
            return ScanResult(broker_slug=self.slug, found=False, error=str(exc))


# ── Registry ──────────────────────────────────────────────────────────────────

BUILTIN_ADAPTERS: dict[str, type[BrokerAdapter]] = {
    PeopleFinderDemoAdapter.slug: PeopleFinderDemoAdapter,
    DataAggregatorDemoAdapter.slug: DataAggregatorDemoAdapter,
    BackgroundCheckDemoAdapter.slug: BackgroundCheckDemoAdapter,
}


def get_adapter(slug: str) -> Optional[BrokerAdapter]:
    """Return an instantiated adapter for *slug*, or ``None`` if not registered."""
    cls = BUILTIN_ADAPTERS.get(slug)
    return cls() if cls else None
